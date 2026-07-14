import re
from datetime import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

from ledger_jester.converter import Amount, CsvConverter, Posting, Transaction


class EnparaConverter(CsvConverter):
    # TODO: We can generalize with the following changes whole converters can
    # be squished mostly to the parent class most of the convert function gets
    # streamlind this way
    # TODO: Balance assertiosn
    COLS = {
        "amount": "İşlem Tutarı (TL)",
        "balance": "Bakiye (TL)",
        "date0": "Tarih",
        "payee": "Açıklama",
    }
    DATE_FORMAT = "%Y-%m-%d"
    FIELDSET = set(COLS.values())

    def __init__(self, *args, **kwargs):
        super(EnparaConverter, self).__init__(*args, **kwargs)
        self.cols = SimpleNamespace(**self.COLS)
        if self.name is None:
            self.name = "Assets:Bank:Enpara:Checking"

    def filter_payee_names(self, payee: str) -> str:
        payee = payee.split(",")[0]
        _prefixes = re.compile(r"\%\S*( kampanyalı)* faiz oranı ile 1 g")
        return re.sub(_prefixes, "G", payee)

    def skip_row(self, row) -> bool:
        return row is None

    def convert(self, row):
        if self.skip_row(row):
            return None

        currency = "TRY"
        date_start = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        amount = Decimal(row[self.cols.amount].replace(",", ""))
        posterior_bal = Decimal(row[self.cols.balance].replace(",", ""))
        meta = {"csvid": self.get_csv_id(row)}

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
            amount=Amount(amount, currency),
            asserted=Amount(posterior_bal, currency),
            metadata=meta,
        )
        postings = [posting_dst, posting_src]

        if not acct_dst:
            postings = postings[1:]

        return Transaction(
            date=date_start,
            cleared=True,
            aux_date=None,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
