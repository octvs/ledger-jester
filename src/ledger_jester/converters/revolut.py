import re
from datetime import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

from ledger_jester.converter import Amount, CsvConverter, Posting, Transaction


class RevolutConverter(CsvConverter):
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
    FIELDSET = set(COLS.values())

    def __init__(self, *args, **kwargs):
        super(RevolutConverter, self).__init__(*args, **kwargs)
        self.cols = SimpleNamespace(**self.COLS)
        if self.name is None:
            self.name = "Assets:Bank:Revolut:Checking"
        # This can be later improved, I don't want to add a new cli flag now
        self.acc_type = "Current"
        if self.name.split(":")[-1] == "Savings":
            self.acc_type = "Deposit"

    def filter_payee_names(self, payee: str) -> str:
        _prefixes = re.compile(r"(From |To |Payment from )")
        payee = re.sub(_prefixes, "", payee)
        _interest_prefix = r"Net interest paid"
        return re.sub(_interest_prefix + r" to .*", _interest_prefix, payee)

    def skip_row(self, row) -> bool:
        return (
            row is None
            or (row["State"] in ["REVERTED", "PENDING"])
            or row["Product"] != self.acc_type
        )

    def convert(self, row):
        if self.skip_row(row):
            return None

        date_start = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        date_comp = dt.strptime(row[self.cols.date1], self.DATE_FORMAT)
        amount = Decimal(row[self.cols.amount])
        fee = Decimal(row[self.cols.fee])
        currency = row[self.cols.currency]
        cleared = row[self.cols.state] == "COMPLETED"
        posterior_bal = Decimal(row[self.cols.balance])
        meta = {"csvid": self.get_csv_id(row)}

        if date_start.date() == date_comp.date():
            date_comp = None

        payee = self.filter_payee_names(row[self.cols.payee])
        payee = self.lgr.get_autosync_payee(payee, self.name)

        acct_src = self.name
        acct_dst = self.mk_dynamic_account(payee)

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

        # If fee given on the FIELDSET, if not skip
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
