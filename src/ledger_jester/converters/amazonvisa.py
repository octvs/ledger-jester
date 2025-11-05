from datetime import datetime as dt
from decimal import Decimal

from ledger_jester.converter import Amount, CsvConverter, Posting, Transaction


class AmazonVisaConverter(CsvConverter):
    FIELDSET = set(
        [
            "Datum",
            "Zeit",
            "Karte",
            "Beschreibung",
            "Umsatzkategorie",
            "Unterkategorie",
            "Betrag",
            "Punkte",
        ]
    )

    def __init__(self, *args, **kwargs):
        super(AmazonVisaConverter, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = "Liabilities:CreditCard:Amazon"

    def get_csv_id(self, row: dict):
        """
        Get csv id for a row ignoring 'Punkte' column.

        Aforementioned column gets updated with a delay around 3-5 days with
        which we don't want to update our logs, hence ignore it for csvid.
        """
        # This later can be revoked in case we start handling the "Punkte" col
        _row = dict(row)
        del _row["Punkte"]
        return super(AmazonVisaConverter, self).get_csv_id(_row)

    def convert(self, row):
        if row is None:
            return None

        date = dt.strptime(row["Datum"], "%d.%m.%Y ")
        _amount, _curr = row["Betrag"].split()
        amount = Decimal(self.eu_decimal_to_us(_amount))
        currency = self.mk_currency(_curr)
        meta = {"csvid": self.get_csv_id(row)}
        payee = self.lgr.get_autosync_payee(row["Beschreibung"], self.name)
        acct_dst = self.mk_dynamic_account(payee, exclude=self.name)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, reverse=True),
        )
        posting_src = Posting(
            account=self.name,
            amount=Amount(amount, currency),
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

    @staticmethod
    def mk_currency(currency):
        if currency == "$":
            currency = "USD"
        elif currency == "£":
            currency = "GBP"
        elif currency == "€":
            currency = "EUR"
        return currency
