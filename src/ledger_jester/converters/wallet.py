from csv import DictReader
from datetime import datetime as dt
from decimal import Decimal

from ledger_jester.converter import Amount, CsvConverter, Posting, Transaction


class WalletConverter(CsvConverter):
    FIELDSET = set(["Date", "Payee", "Amount", "Currency", "Balance"])

    def __init__(self, *args, **kwargs):
        super(WalletConverter, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = "Assets:Cash:Wallet"
        self.date = None

    @staticmethod
    def mk_currency(currency):
        return "EUR" if currency == "" else currency

    def preprocess(self, reader: DictReader) -> list[dict]:
        """
        Preprocess logs to deduce date.

        Since csv logs for wallet are intended to be written by hand this
        converter allows user to abstain year and month parts of a date if it
        is same with the first row of the csv. For this purpose we set the
        class date variable ("%Y%m") from the first row.
        """
        _reader = list(reader)
        month_year_string = _reader[0]["Date"][:6]  # assuming %Y%m%d
        for row in _reader:
            row["Date"] = self.mk_date(row["Date"], month_year_string)
        return _reader

    @staticmethod
    def mk_date(date, month_year):
        if len(date) == 2:
            date = month_year + date
        elif len(date) == 4:
            date = month_year[:4] + date
        return date

    def convert(self, row):
        if row is None:
            return None

        date = dt.strptime(row["Date"], "%Y%m%d")
        amount = Decimal(row["Amount"])
        currency = self.mk_currency(row["Currency"])
        bal = Decimal(row["Balance"]) if row["Balance"] != "" else None
        meta = {"csvid": self.get_csv_id(row)}
        payee = self.lgr.get_autosync_payee(row["Payee"], self.name)
        acct_dst = self.mk_dynamic_account(payee, exclude=self.name)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, reverse=True),
        )
        posting_src = Posting(
            account=self.name,
            amount=Amount(amount, currency),
            asserted=Amount(bal, currency) if bal else None,
            metadata=meta,
        )

        postings = [posting_dst, posting_src]

        return Transaction(
            date=date,
            cleared=True,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
