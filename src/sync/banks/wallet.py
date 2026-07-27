"""Converter implementation for wallet csv journals."""

from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import override

from ledger_wrapper import Amount, Posting, Transaction
from sync import REGISTRY, CsvConverter, CsvRow


@dataclass
class WalletRow(CsvRow):
    """Dataclass representing a transaction row from cash journals."""

    date: str = field(metadata={"col": "Date"})
    payee: str = field(metadata={"col": "Payee"})
    amount: str = field(metadata={"col": "Amount"})
    currency: str = field(metadata={"col": "Currency"})
    balance: str = field(metadata={"col": "Balance"})

    def __post_init__(self) -> None:
        """If currency is empty or whitespace, default to EUR."""
        if not self.currency:
            self.currency = "EUR"


@REGISTRY.register
class WalletConverter(CsvConverter[WalletRow]):
    """Converter class for hand-written csv journals to track cash."""

    TYPE = "wallet"
    ROW_TYPE = WalletRow
    DATE_FORMAT = "%Y%m%d"

    @override
    def convert(self, row: WalletRow) -> Transaction:
        """Convert given wallet journal row to a Transaction object."""
        date = dt.strptime(row.date, self.DATE_FORMAT)
        acct_dst = self.get_account_by_payee(row.payee)

        posting_src = Posting(
            account=self.acc_name,
            amount=Amount(row.amount, row.currency),
            asserted=Amount(row.balance, row.currency)
            if row.balance
            else None,
            metadata={"csvid": row.csvid},
        )
        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(row.amount, row.currency, invert=True),
        )

        postings = [posting_dst, posting_src]

        return Transaction(
            date=date,
            cleared=True,
            payee=row.payee,
            postings=postings,
        )
