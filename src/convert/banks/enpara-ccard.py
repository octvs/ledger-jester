"""Converter implementation for Enpara Credit Card csv statements."""

from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import override

from convert import REGISTRY, CsvConverter, CsvRow
from ledger_wrapper import Amount, Posting, Transaction


@dataclass
class EnparaCCRow(CsvRow):
    """Dataclass representing a transaction row from Enpara CCard exports."""

    date: str = field(metadata={"col": "İşlem Tarihi"})
    payee: str = field(metadata={"col": "Açıklama"})
    raw_amount: str = field(metadata={"col": "Tutar"})

    # Processed attributes
    amount: str = field(init=False)
    currency: str = field(init=False)

    def __post_init__(self) -> None:
        """Set currency by default to TRY."""
        # Remove whitespace after negative sign if present before spliting
        _raw_amount = self.raw_amount.replace("- ", "-").split(" ")
        self.amount = self.format_eu_number_to_us(_raw_amount[0])
        self.currency = self.make_currency(_raw_amount[1])


@REGISTRY.register
class EnparaCCConverter(CsvConverter[EnparaCCRow]):
    """Converter class for Enpara Credit Card csv statements."""

    TYPE = "enparacc"
    ROW_TYPE = EnparaCCRow
    DATE_FORMAT = "%d/%m/%Y"

    @override
    def convert(self, row: EnparaCCRow) -> Transaction:
        """Convert given Enpara CCard export row to a Transaction object."""
        date_start = dt.strptime(row.date, self.DATE_FORMAT)
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

        return Transaction(
            date=date_start,
            cleared=True,
            payee=row.payee,
            postings=postings,
        )
