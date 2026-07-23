"""Converter implementation for Amazon Visa csv statements."""

from datetime import datetime as dt
from typing import override

from ledger_wrapper import Amount, Posting, Transaction
from sync import REGISTRY
from sync.converter import CsvConverter


@REGISTRY.register
class AmazonVisaConverter(CsvConverter):
    """Converter class for Amazon Visa csv statements.

    Currently disregards "Punkte" column which holds amazon points for the
    transcation.
    """

    TYPE = "amazonvisa"
    COLS = {
        "date0": "Datum",
        "_": "Zeit",
        "_1": "Karte",
        "payee": "Beschreibung",
        "_2": "Umsatzkategorie",
        "_3": "Unterkategorie",
        "amount": "Betrag",
        "_4": "Punkte",
    }
    DATE_FORMAT = "%d.%m.%Y "

    @override
    def get_identifier(self, row: dict) -> str:
        """Exclude 'Punkte' before passing row to parent class for hashing.

        Aforementioned column gets updated couple of days after the
        transaction. This triggers another sync for the same transaction, which
        we avoid by dropping it before hash calculation.
        """
        clean_row = {k: v for k, v in row.items() if k != "Punkte"}
        return super().get_identifier(clean_row)

    @override
    def convert(self, row: dict) -> Transaction:
        """Convert given Amazon Visa export row to a Transaction object."""
        date = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        _amount, _curr = row["Betrag"].split()
        amount = self.format_eu_number_to_us(_amount)
        currency = self.make_currency(_curr)
        payee = row[self.cols.payee]
        meta = {"csvid": self.get_identifier(row)}
        acct_src = self.acc_name
        acct_dst = self.get_account_by_payee(payee)

        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount, currency),
            metadata=meta,
        )
        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, invert=True),
        )
        postings = [posting_dst, posting_src]

        return Transaction(
            date=date,
            cleared=True,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
