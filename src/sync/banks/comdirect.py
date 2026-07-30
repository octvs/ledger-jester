"""Converter implementation for Comdirect csv statements."""

import re
from dataclasses import dataclass, field
from datetime import datetime as dt
from functools import cached_property
from typing import override

from ledger_wrapper import Amount, Posting, Transaction
from sync import REGISTRY, CsvConverter, CsvRow


@dataclass
class ComdirectRow(CsvRow):
    """Dataclass representing a transaction row from Comdirect exports."""

    date: str = field(metadata={"col": "Buchungstag"})
    date_comp: str = field(metadata={"col": "Wertstellung (Valuta)"})
    payee: str = field(metadata={"col": "Vorgang"})
    details: str = field(metadata={"col": "Buchungstext"})
    raw_amount: str = field(metadata={"col": "Umsatz in EUR"})

    # Processed attributes
    amount: str = field(init=False)
    currency: str = field(init=False)

    def __post_init__(self) -> None:
        """Set currency by default to EUR and reformat amount decimal comma."""
        self.currency = "EUR"  # TODO: Is this embedded on the source file?
        self.amount = self.format_eu_number_to_us(self.raw_amount)

    @override
    @cached_property
    def csvid(self) -> str:
        """Extract the reference number from details field."""
        return f"comdirect.{re.findall(r'Ref\.\s(\S+)', self.details)[0]}"


@REGISTRY.register
class ComdirectConverter(CsvConverter[ComdirectRow]):
    """Converter class for Comdirect csv statements."""

    TYPE = "comdirect"
    ROW_TYPE = ComdirectRow
    DATE_FORMAT = "%d.%m.%Y"

    @override
    def convert(self, row: ComdirectRow) -> Transaction:
        """Convert given Comdirect export row to a Transaction object."""
        date_start = dt.strptime(row.date, self.DATE_FORMAT)
        date_comp = dt.strptime(row.date_comp, self.DATE_FORMAT)
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

        if date_start.date() == date_comp.date():
            date_comp = None

        return Transaction(
            date=date_start,
            cleared=True,
            aux_date=date_comp,
            payee=row.payee,
            postings=postings,
        )
