"""Converter implementation for Revolut csv exports."""

import csv
import hashlib
from collections import Counter, defaultdict
from datetime import datetime as dt
from types import SimpleNamespace

from ledger_wrapper import Amount, Ledger, Posting, Transaction
from sync import REGISTRY


@REGISTRY.register
class RevolutConverter:
    """Converter implementation for Revolut csv exports."""

    TYPE = "revolut"
    COLS = {
        "_": "Type",
        "acc_type": "Product",
        "date0": "Started Date",
        "date1": "Completed Date",
        "payee": "Description",
        "amount": "Amount",
        "fee": "Fee",
        "currency": "Currency",
        "state": "State",
        "balance": "Balance",
    }
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, account: str) -> None:
        """Initialize converter with the target account name.

        Additionally:
        - Casts COLS class attribute to a SimpleNamespace for easier access.
        - Loads payees via self.load_payees.
        - Loads already synchronized xact ids via Ledger.fetch_all_metadata.
        """
        self.ledger: Ledger = Ledger()
        self.cols: SimpleNamespace = SimpleNamespace(**self.COLS)
        self.acc_name: str = account
        self._payees: defaultdict = defaultdict(list)
        self.load_payees()
        self._synced_ids = self.ledger.fetch_all_metadata("csvid")

    def load_payees(self) -> None:
        """Load all related payee names to the target account.

        Runs Ledger.run_query, to create a subprocess that runs: `ledger csv
        --related <acc_name>`.
        """
        ret = self.ledger.run_query(["csv", "--related", self.acc_name])
        for line in csv.reader(ret.splitlines()):
            payee, dst_account = line[2:4]
            self._payees[payee].append(dst_account)

    def get_account_by_payee(self, payee: str) -> str:
        """Get the most probable payee name via frequency."""
        if payee in self._payees.keys():
            return Counter(self._payees[payee]).most_common(1)[0][0]
        return "Expenses:Misc"

    def get_identifier(self, row: dict) -> str:
        """Calculate the md5 hash sum of the given row.

        Sorts dictionary before writing updating hash object with each element.
        Also encodes each dictionary element to utf-8 for consistency.
        """
        h = hashlib.md5()
        for key in sorted(row.keys()):
            h.update((f"{key}={row[key]}\n").encode("utf-8"))
        return h.hexdigest()

    def is_row_synced(self, row: dict) -> bool:
        """Check whether the given row is in already synchronized id list."""
        return self.get_identifier(row) in self._synced_ids

    def convert(self, row: dict) -> Transaction | None:
        """Convert given Revolut export row to a Transaction object."""
        # TODO: generic skip_row():
        if (
            row is None
            or row["Product"] == "Deposit"
            or (row["State"] in ["REVERTED", "PENDING"])
        ):
            return None

        date_start = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        date_comp = dt.strptime(row[self.cols.date1], self.DATE_FORMAT)
        amount = row[self.cols.amount]
        fee = row[self.cols.fee]
        currency = row[self.cols.currency]
        cleared = row[self.cols.state] == "COMPLETED"
        posterior_bal = row[self.cols.balance]
        payee = row[self.cols.payee]
        meta = {"csvid": self.get_identifier(row)}
        acct_src = self.acc_name
        acct_dst = self.get_account_by_payee(payee)

        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount, currency) - Amount(fee, currency),
            asserted=Amount(posterior_bal, currency),
            metadata=meta,
        )
        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, invert=True),
        )
        posting_fee = Posting(
            "Expenses:Finance:Revolut", Amount(fee, currency)
        )
        postings = [posting_dst, posting_src]

        # If fee given on the FIELDSET, if not skip
        if Amount(fee, currency) > 0:
            postings.append(posting_fee)
        if date_start.date() == date_comp.date():
            date_comp = None

        return Transaction(
            date=date_start,
            cleared=cleared,
            aux_date=date_comp,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
