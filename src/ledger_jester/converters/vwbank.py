import re
from datetime import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

from ledger_jester.converter import Amount, CsvConverter, Posting, Transaction


class VWBankConverter(CsvConverter):
    COLS = {
        "date0": "Wertstellung",
        "date1": "Buchungsdatum",
        "payee": "Umsatzart",
        "detail": "Umsatzinformation",
        "__": "Referenznummer",
        "amount": "Umsatz",
    }
    DATE_FORMAT = "%d.%m.%Y"
    FIELDSET = set(COLS.values())

    def __init__(self, *args, **kwargs):
        super(VWBankConverter, self).__init__(*args, **kwargs)
        self.cols = SimpleNamespace(**self.COLS)
        self.name = "Assets:Bank:VWBank"

    def skip_row(self, row) -> bool:
        return row is None

    def convert(self, row):
        if self.skip_row(row):
            return None

        date_start = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        date_comp = dt.strptime(row[self.cols.date1], self.DATE_FORMAT)
        amount = Decimal(self.eu_decimal_to_us(row[self.cols.amount]))
        meta = {
            "csvid": self.get_csv_id(row),
            "reference": row[self.cols.detail],
        }
        payee = self.lgr.get_autosync_payee(row[self.cols.payee], self.name)
        currency = "EUR"

        if date_start.date() == date_comp.date():
            date_comp = None

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
            aux_date=date_comp,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
