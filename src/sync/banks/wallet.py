"""Converter implementation for wallet csv journals."""

from datetime import datetime as dt
from typing import override

from ledger_wrapper import Amount, Posting, Transaction
from sync import REGISTRY, CsvConverter


@REGISTRY.register
class WalletConverter(CsvConverter):
    """Converter class for hand-written csv journals to track cash."""

    TYPE = "wallet"
    COLS = {
        "date0": "Date",
        "payee": "Payee",
        "amount": "Amount",
        "currency": "Currency",
        "balance": "Balance",
    }
    DATE_FORMAT = "%Y%m%d"

    @override
    def make_currency(self, currency: str) -> str:
        """Return euro if empty, otherwise defer to func from parent class."""
        return "EUR" if currency == "" else super().make_currency(currency)

    @override
    def convert(self, row: dict) -> Transaction:
        """Convert given wallet journal row to a Transaction object."""
        date = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        amount = row[self.cols.amount]
        currency = self.make_currency(row[self.cols.currency])
        posteior_bal = (
            row[self.cols.balance] if row[self.cols.balance] else None
        )
        payee = row[self.cols.payee]
        meta = {"csvid": self.get_identifier(row)}
        acct_src = self.acc_name
        acct_dst = self.get_account_by_payee(payee)

        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount, currency),
            asserted=Amount(posteior_bal, currency) if posteior_bal else None,
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
            payee=payee,
            postings=postings,
        )
