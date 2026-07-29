"""Converter implementation for Paypal csv statements."""

from dataclasses import dataclass, field
from datetime import datetime as dt
from functools import cached_property
from typing import override

from ledger_wrapper import Amount, Posting, Transaction
from sync import REGISTRY, CsvConverter, CsvRow


@dataclass
class PaypalRow(CsvRow):
    """Dataclass representing a transaction row from Paypal exports."""

    date: str = field(metadata={"col": "Date"})
    time: str = field(metadata={"col": "Time"})
    time_zone: str = field(metadata={"col": "Time Zone"})
    description: str = field(metadata={"col": "Description"})
    currency: str = field(metadata={"col": "Currency"})
    amount: str = field(metadata={"col": "Net"})
    balance: str = field(metadata={"col": "Balance"})
    xact_id: str = field(metadata={"col": "Transaction ID"})
    payee: str = field(metadata={"col": "Name"})
    fee: str = field(metadata={"col": "Fee"})

    def __post_init__(self) -> None:
        """Convert number formats, use Description column if Name is empty."""
        if not self.payee:
            self.payee = self.description
        self.amount = self.format_eu_number_to_us(self.amount)
        self.fee = self.format_eu_number_to_us(self.fee)
        self.balance = self.format_eu_number_to_us(self.balance)

    @override
    @cached_property
    def csvid(self) -> str:
        """Use the transaction ID provided by paypal."""
        return f"comdirect.{self.xact_id}"


@REGISTRY.register
class PaypalConverter(CsvConverter[PaypalRow]):
    """Converter class for Paypal csv statements."""

    TYPE = "paypal"
    ROW_TYPE = PaypalRow
    DATE_FORMAT = "%d.%m.%Y"

    @override
    def convert(self, row: PaypalRow) -> Transaction:
        """Convert given Paypal export row to a Transaction object."""
        date_start = dt.strptime(row.date, self.DATE_FORMAT)
        acct_dst = self.get_account_by_payee(row.payee)

        posting_src = Posting(
            account=self.acc_name,
            amount=Amount(row.amount, row.currency)
            - Amount(row.fee, row.currency),
            asserted=Amount(row.balance, row.currency),
            metadata={"csvid": row.csvid},
        )
        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(row.amount, row.currency, invert=True),
        )
        postings = [posting_dst, posting_src]

        fee = Amount(row.fee, row.currency)
        if fee > 0:
            postings.append(
                Posting(f"Expenses:Finance:{self.TYPE.capitalize()}", fee)
            )

        return Transaction(
            date=date_start,
            cleared=True,
            payee=row.payee,
            postings=postings,
        )
