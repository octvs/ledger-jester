"""Converter implementation for Volkswagen Bank csv statements."""

from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import override

from ledger_wrapper import Amount, Posting, Transaction
from sync import REGISTRY, CsvConverter, CsvRow


@dataclass
class VWBankRow(CsvRow):
    """Dataclass representing a transaction row from VWBank exports."""

    date: str = field(metadata={"col": "Buchungsdatum"})
    payee: str = field(metadata={"col": "Umsatzart"})
    date_comp: str = field(metadata={"col": "Wertstellung"})
    _amount0: str = field(metadata={"col": "Soll (EUR)"})
    _amount1: str = field(metadata={"col": "Haben (EUR)"})

    def __post_init__(self) -> None:
        """Set default currency to EUR, merge two amount columns to single."""
        self.currency = "EUR"
        _amount = self._amount1
        if not _amount:
            _amount = "-" + self._amount0
        self.amount = self.format_eu_number_to_us(_amount)


@REGISTRY.register
class VWBankConverter(CsvConverter[VWBankRow]):
    """Converter class for VWBank csv statements."""

    TYPE = "vwbank"
    ROW_TYPE = VWBankRow
    DATE_FORMAT = "%d.%m.%Y"

    @override
    def convert(self, row: VWBankRow) -> Transaction:
        """Convert given VWBank export row to a Transaction object."""
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
