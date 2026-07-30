"""Converter implementation for Cepteteb csv statements."""

from dataclasses import dataclass, field
from datetime import datetime as dt
from functools import cached_property
from typing import override

from ledger_wrapper import Amount, Posting, Transaction
from sync import REGISTRY, CsvConverter, CsvRow


@dataclass
class CeptetebRow(CsvRow):
    """Dataclass representing a transaction row from Cepteteb exports."""

    date: str = field(metadata={"col": "Tarih"})
    date_comp: str = field(metadata={"col": "Valör"})
    time: str = field(metadata={"col": "Saat"})
    payee: str = field(metadata={"col": "Açıklama"})
    amount: str = field(metadata={"col": "Tutar"})
    balance: str = field(metadata={"col": "Bakiye"})
    id: str = field(metadata={"col": "Dekont"})
    currency: str = field(metadata={"col": "Kur"})

    def __post_init__(self) -> None:
        """Map currency codes to versions used in ledger-jester."""
        self.currency = self.make_currency(self.currency)

    @override
    @cached_property
    def csvid(self) -> str:
        """Set id provided by bank to csvid.

        Same id int is given for xacts between two sub-accounts, where
        synchronizing one would make the other appear already synced. To
        differentiate them the function attaches a suffix by checking whether
        currency is set to another value.
        """
        _suffix = "eur" if self.currency == "EUR" else ""
        return f"cepteteb{_suffix}.{self.id}"


@REGISTRY.register
class CeptetebConverter(CsvConverter[CeptetebRow]):
    """Converter class for Cepteteb csv statements."""

    TYPE = "cepteteb"
    ROW_TYPE = CeptetebRow
    DATE_FORMAT = "%d/%m/%Y"

    @override
    def convert(self, row: CeptetebRow) -> Transaction:
        """Convert given Cepteteb export row to a Transaction object."""
        date_start = dt.strptime(row.date, self.DATE_FORMAT)
        date_comp = dt.strptime(row.date_comp, self.DATE_FORMAT)
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

        if date_start.date() == date_comp.date():
            date_comp = None

        return Transaction(
            date=date_start,
            cleared=True,
            aux_date=date_comp,
            payee=row.payee,
            postings=postings,
        )
