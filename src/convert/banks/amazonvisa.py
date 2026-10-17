"""Converter implementation for Amazon Visa csv statements."""

from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import override

from convert import REGISTRY, CsvConverter, CsvRow
from ledger_wrapper import Amount, Posting, Transaction


@dataclass
class AmazonVisaRow(CsvRow):
    """Dataclass representing a transaction row from Amazon Visa exports."""

    date: str = field(metadata={"col": "Datum"})
    payee: str = field(metadata={"col": "Beschreibung"})
    raw_amount: str = field(metadata={"col": "Betrag"})
    points: str = field(metadata={"col": "Punkte"})

    # Processed attributes
    amount: str = field(init=False)
    currency: str = field(init=False)

    def __post_init__(self) -> None:
        """Parse raw amount string into separate amount and currency."""
        _amount, _currency = self.raw_amount.split()
        self.amount = self.format_eu_number_to_us(_amount)
        self.currency = self.make_currency(_currency)


@REGISTRY.register
class AmazonVisaConverter(CsvConverter[AmazonVisaRow]):
    """Converter class for Amazon Visa csv statements."""

    TYPE = "amazonvisa"
    ROW_TYPE = AmazonVisaRow
    DATE_FORMAT = "%d.%m.%Y "

    @override
    def convert(self, row: AmazonVisaRow) -> Transaction:
        """Convert given Amazon Visa export row to a Transaction object."""
        date = dt.strptime(row.date, self.DATE_FORMAT)
        acct_dst = self.get_account_by_payee(row.payee)

        posting_src = Posting(
            account=self.acc_name,
            amount=Amount(row.amount, row.currency),
            metadata={"csvid": row.csvid},
        )
        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(row.amount, row.currency, invert=True),
        )
        postings = [posting_dst, posting_src]

        points = Amount(row.points, "AMZPT")
        if points != 0:
            point_postings = [
                Posting("Equity:Amazon Points", points),
                Posting(
                    "Equity:Credit Card Rewards",
                    Amount(row.points, "AMZPT", invert=True),
                ),
            ]
            if postings[0].amount == 0:  # xact only w/ points
                postings = []
                point_postings[1].metadata = {"csvid": row.csvid}  # keep csvid

            postings += point_postings

        return Transaction(
            date=date,
            cleared=True,
            payee=row.payee,
            postings=postings,
        )
