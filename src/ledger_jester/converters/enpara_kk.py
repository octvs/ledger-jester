from datetime import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

from ledger_jester.converter import Amount, CsvConverter, Posting, Transaction


class EnparaCCConverter(CsvConverter):
    COLS = {
        "amount": "Tutar",
        "date0": "İşlem Tarihi",
        "payee": "Açıklama",
    }
    DATE_FORMAT = "%d/%m/%Y"
    FIELDSET = set(COLS.values())

    def __init__(self, *args, **kwargs):
        super(EnparaCCConverter, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = "Liabilities:CreditCard:Enpara"
        self.cols = SimpleNamespace(**self.COLS)

    def read_amount(self, cell):
        return Decimal(self.eu_decimal_to_us(cell.split(" ")[0])) * -1

    def convert(self, row):
        if row is None:
            return None

        currency = "TRY"
        date_start = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        amount = self.read_amount(row[self.cols.amount])
        meta = {"csvid": self.get_csv_id(row)}

        payee = self.filter_payee_names(row[self.cols.payee])
        payee = self.lgr.get_autosync_payee(payee, self.name)

        acct_src = self.name
        acct_dst = self.mk_dynamic_account(payee, exclude=acct_src)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, reverse=True),
        )
        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount, currency),
            metadata=meta,
        )
        postings = [posting_dst, posting_src]

        return Transaction(
            date=date_start,
            cleared=True,
            aux_date=None,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
