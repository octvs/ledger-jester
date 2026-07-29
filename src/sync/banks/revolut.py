"""Converter implementation for Revolut csv statements."""

import re
from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import override

from ledger_wrapper import Amount, Posting, Transaction
from sync import REGISTRY, CsvConverter, CsvRow


@dataclass
class RevolutRow(CsvRow):
    """Dataclass representing a transaction row from Revolut exports."""

    acc_type: str = field(metadata={"col": "Product"})
    date: str = field(metadata={"col": "Started Date"})
    date_comp: str = field(metadata={"col": "Completed Date"})
    payee: str = field(metadata={"col": "Description"})
    amount: str = field(metadata={"col": "Amount"})
    fee: str = field(metadata={"col": "Fee"})
    currency: str = field(metadata={"col": "Currency"})
    state: str = field(metadata={"col": "State"})
    balance: str = field(metadata={"col": "Balance"})

    def __post_init__(self) -> None:
        """Remove date string from payee to allow matching across dates."""
        _prefix = 'Net interest paid to "Instant Access Savings"'
        self.payee = re.sub(_prefix + ".*$", _prefix, self.payee)


@REGISTRY.register
class RevolutConverter(CsvConverter[RevolutRow]):
    """Converter class for Revolut csv statements.

    The converter guesses which account to use from the export (Deposit or
    Current) based on the account name provided on the initialization. If given
    account name ends with "Savings" it uses rows for "Deposit", if "Checking"
    "Current".
    """

    TYPE = "revolut"
    ROW_TYPE = RevolutRow
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    _ACC_MAP = {"Checking": "Current", "Savings": "Deposit"}

    @override
    def skip_row(self, row: RevolutRow) -> bool:
        """Skip rows based on extended conditions for revolut.

        Skips the current row if:
        - "Product" column is not the target for the current invocation.
        - "State" column is either "REVERTED" or "PENDING".
        """
        curr_type = self._ACC_MAP[self.acc_name.split(":")[-1]]
        return (
            row.acc_type != curr_type
            or row.state in ["REVERTED", "PENDING"]
            or super().skip_row(row)
        )

    @override
    def convert(self, row: RevolutRow) -> Transaction:
        """Convert given Revolut export row to a Transaction object."""
        date_start = dt.strptime(row.date, self.DATE_FORMAT)
        date_comp = dt.strptime(row.date_comp, self.DATE_FORMAT)
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

        if date_start.date() == date_comp.date():
            date_comp = None

        return Transaction(
            date=date_start,
            cleared=row.state == "COMPLETED",
            aux_date=date_comp,
            payee=row.payee,
            postings=postings,
        )
