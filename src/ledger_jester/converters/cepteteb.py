import logging
import re
from datetime import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

from ledger_jester.converter import (
    Amount,
    Converter,
    CsvConverter,
    Posting,
    Transaction,
)


class CeptetebConverter(CsvConverter):
    COLS = {
        "amount": "Tutar",
        "balance": "Bakiye",
        "date0": "Tarih",
        "date1": "Valör",
        "payee": "Açıklama",
        "ref": "Dekont",
    }
    DATE_FORMAT = "%Y-%m-%d"
    FIELDSET = set(COLS.values())

    def __init__(self, *args, **kwargs):
        super(CeptetebConverter, self).__init__(*args, **kwargs)
        self.cols = SimpleNamespace(**self.COLS)
        self.currency = "TRY"
        if self.name is None:
            self.name = "Assets:Bank:Teb:Checking"
        elif self.name.split(":")[-1] == "EUR":
            self.currency = "EUR"

    def get_csv_id(self, row):
        return f"cepteteb.{Converter.clean_id(row['Dekont'])}"

    def convert(self, row):
        if self.skip_row(row):
            return None

        date_start = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        date_comp = dt.strptime(row[self.cols.date1], self.DATE_FORMAT)
        amount = Decimal(row[self.cols.amount])
        posterior_bal = Decimal(row[self.cols.balance])
        meta = {"csvid": self.get_csv_id(row)}

        if date_start.date() == date_comp.date():
            date_comp = None

        payee = self.filter_payee_names(row[self.cols.payee])
        payee = self.lgr.get_autosync_payee(payee, self.name)

        acct_src = self.name
        acct_dst = self.mk_dynamic_account(payee, exclude=acct_src)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, self.currency, reverse=True),
        )
        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount, self.currency),
            asserted=Amount(posterior_bal, self.currency),
            metadata=meta,
        )
        postings = [posting_dst, posting_src]

        if not acct_dst:
            postings = postings[1:]

        return Transaction(
            date=date_start,
            cleared=True,
            aux_date=date_comp,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
