"""Converter implementation for Revolut csv statements."""

from datetime import datetime as dt
from typing import override

from ledger_wrapper import Amount, Posting, Transaction
from sync import REGISTRY, CsvConverter


@REGISTRY.register
class RevolutConverter(CsvConverter):
    """Converter class for Revolut csv statements.

    The converter guesses which account to use from the export (Deposit or
    Current) based on the account name provided on the initialization. If given
    account name ends with "Savings" it uses rows for "Deposit", if "Checking"
    "Current".
    """

    TYPE = "revolut"
    COLS = {
        "_": "Type",
        "acc_type": "Product",
        "date0": "Started Date",
        "date1": "Completed Date",
        "payee": "Description",
        "amount": "Amount",
        "fee": "Fee",
        "currency": "Currency",
        "state": "State",
        "balance": "Balance",
    }
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    _ACC_MAP = {"Checking": "Current", "Savings": "Deposit"}

    @override
    def skip_row(self, row: dict) -> bool:
        """Skip rows based on extended conditions for revolut.

        Skips the current row if:
        - "Product" column is not the target for the current invocation.
        - "State" column is either "REVERTED" or "PENDING".
        """
        curr_type = self._ACC_MAP[self.acc_name.split(":")[-1]]
        return (
            row[self.cols.acc_type] != curr_type
            or row[self.cols.state] in ["REVERTED", "PENDING"]
            or super().skip_row(row)
        )

    @override
    def convert(self, row: dict) -> Transaction:
        """Convert given Revolut export row to a Transaction object."""
        date_start = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        date_comp = dt.strptime(row[self.cols.date1], self.DATE_FORMAT)
        amount = row[self.cols.amount]
        fee = row[self.cols.fee]
        currency = row[self.cols.currency]
        cleared = row[self.cols.state] == "COMPLETED"
        posterior_bal = row[self.cols.balance]
        payee = row[self.cols.payee]
        meta = {"csvid": self.get_identifier(row)}
        acct_src = self.acc_name
        acct_dst = self.get_account_by_payee(payee)

        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount, currency) - Amount(fee, currency),
            asserted=Amount(posterior_bal, currency),
            metadata=meta,
        )
        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, invert=True),
        )
        posting_fee = Posting(
            "Expenses:Finance:Revolut", Amount(fee, currency)
        )
        postings = [posting_dst, posting_src]

        # If fee given on the FIELDSET, if not skip
        if Amount(fee, currency) > 0:
            postings.append(posting_fee)
        if date_start.date() == date_comp.date():
            date_comp = None

        return Transaction(
            date=date_start,
            cleared=cleared,
            aux_date=date_comp,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
