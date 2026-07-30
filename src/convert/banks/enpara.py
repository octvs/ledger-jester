"""Converter implementation for Enpara csv statements."""

import re
from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import override

from convert import REGISTRY, CsvConverter, CsvRow
from ledger_wrapper import Amount, Posting, Transaction


@dataclass
class EnparaRow(CsvRow):
    """Dataclass representing a transaction row from Enpara exports."""

    date: str = field(metadata={"col": "Tarih"})
    payee: str = field(metadata={"col": "Açıklama"})
    amount: str = field(metadata={"col": "İşlem Tutarı (TL)"})
    balance: str = field(metadata={"col": "Bakiye (TL)"})

    # Processed attributes
    currency: str = field(init=False)

    PAYEE_FILTERS: tuple[tuple[re.Pattern, str], ...] = (
        # Strip bank transaction details after comma from transfers
        (re.compile(r"\s*,.*$"), ""),
        # Strip extra details from interest payment
        (re.compile(r"\%\S*( kampanyalı)* faiz oranı ile 1 g"), "G"),
    )

    def __post_init__(self) -> None:
        """Set currency by default to TRY, filter payee names."""
        self.currency = "TRY"
        for pattern, replacement in self.PAYEE_FILTERS:
            self.payee = pattern.sub(replacement, self.payee)


@REGISTRY.register
class EnparaConverter(CsvConverter[EnparaRow]):
    """Converter class for Enpara csv statements."""

    TYPE = "enpara"
    ROW_TYPE = EnparaRow
    DATE_FORMAT = "%d/%m/%Y"

    @override
    def convert(self, row: EnparaRow) -> Transaction:
        """Convert given Enpara export row to a Transaction object."""
        date_start = dt.strptime(row.date, self.DATE_FORMAT)
        acct_dst = self.get_account_by_payee(row.payee)

        posting_src = Posting(
            account=self.acc_name,
            amount=Amount(row.amount, row.currency),
            asserted=Amount(row.balance, row.currency),
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
