"""TODO."""

import hashlib
from datetime import datetime as dt
from types import SimpleNamespace

from ledger_jester.ledger_wrapper import Amount, Ledger, Posting, Transaction


class RevolutConverter:
    """TODO."""

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

    def __init__(self, account):
        """TODO."""
        self.ledger = Ledger()
        self.cols = SimpleNamespace(**self.COLS)
        self.acc_name = account

    def get_identifier(self, row):
        """TODO."""
        h = hashlib.md5()
        for key in sorted(row.keys()):
            h.update(("%s=%s\n" % (key, row[key])).encode("utf-8"))
        return h.hexdigest()

    def is_row_synced(self, row):
        """TODO."""
        a = self.ledger.match_metadata("csvid", self.get_identifier(row))
        return len(a) > 0

    def convert(self, row):
        """TODO."""
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
        acct_dst = "Expenses:Misc"  # TODO: dynamic_account

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
