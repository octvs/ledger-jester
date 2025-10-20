import re
from csv import DictReader
from datetime import datetime as dt
from decimal import Decimal

from ledger_jester.converter import Amount, CsvConverter, Posting, Transaction


class RevolutConverter(CsvConverter):
    FIELDSET = set(
        [
            "Type",
            "Product",
            "Started Date",
            "Completed Date",
            "Description",
            "Amount",
            "Fee",
            "Currency",
            "State",
            "Balance",
        ]
    )

    def __init__(self, *args, **kwargs):
        super(RevolutConverter, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = "Assets:Bank:Revolut"

    def preprocess(self, reader: DictReader) -> list[dict]:
        """
        Preprocess logs to sort based on date and account type.

        The converter expects the cross postings between current and deposit
        account to be consequent. This is required for balance assertions for
        the latter to work.
        """
        return sorted(reader, key=lambda x: x["Completed Date"] + x["Product"])

    def filter_payee_names(self, payee: str) -> str:
        _prefixes = re.compile(r"(From |To |Payment from )")
        return re.sub(_prefixes, "", payee)

    def convert(self, row):
        # Ignore reverted xacts
        if row is None or (row["State"] in ["REVERTED", "PENDING"]):
            return None

        date_start = dt.strptime(row["Started Date"], "%Y-%m-%d %H:%M:%S")
        date_comp = dt.strptime(row["Completed Date"], "%Y-%m-%d %H:%M:%S")
        amount = Decimal(row["Amount"])
        fee = Decimal(row["Fee"])
        currency = row["Currency"]
        cleared = row["State"] == "COMPLETED"
        posterior_bal = Decimal(row["Balance"])
        meta = {"csvid": self.get_csv_id(row)}

        if date_start.date() == date_comp.date():
            date_comp = None

        payee = self.filter_payee_names(row["Description"])
        payee = self.lgr.get_autosync_payee(payee, self.name)

        if row["Product"] == "Deposit":
            acct_src = self.name + ":Savings"
            if row["Type"] == "Transfer":  # Cross xact, use as bal assertion
                amount = Decimal("0.0")
                acct_dst = None
            else:
                assert row["Type"] == "Interest"  # Rest is not implemented.
                acct_dst = "Income:Interest:Revolut"
        else:
            acct_src = self.name + ":Checking"
            acct_dst = self.mk_dynamic_account(payee, exclude=acct_src)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, reverse=True),
        )
        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount - fee, currency),
            asserted=Amount(posterior_bal, currency),
            metadata=meta,
        )
        posting_fee = Posting(
            "Expenses:Finance:Revolut", Amount(fee, currency)
        )
        postings = [posting_dst, posting_src]

        if not acct_dst:
            postings = postings[1:]

        if fee > 0:
            postings.append(posting_fee)

        return Transaction(
            date=date_start,
            cleared=cleared,
            aux_date=date_comp,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
