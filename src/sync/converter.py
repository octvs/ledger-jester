"""Base converter implementation for csv statements."""

import csv
import hashlib
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from types import SimpleNamespace

from ledger_wrapper import Ledger, Transaction


class CsvConverter(ABC):
    """Generic converter class for csv statements."""

    COLS = {}
    CURRENCY_CODES = {"$": "USD", "£": "GBP", "€": "EUR"}

    def __init__(self, account: str) -> None:
        """Initialize converter with the target account name.

        Additionally
        - Casts COLS class attribute to a SimpleNamespace for easier access.
        - Loads payees via self.load_payees.
        - Loads already synchronized xact ids via Ledger.fetch_all_metadata.

        Args:
            account: Target account name.

        """
        self.ledger: Ledger = Ledger()
        self.cols: SimpleNamespace = SimpleNamespace(**self.COLS)
        self.acc_name: str = account
        self._payees: defaultdict = defaultdict(list)
        self.load_payees()
        self._synced_ids = self.ledger.fetch_all_metadata("csvid")

    def load_payees(self) -> None:
        """Load all related payee names to the target account.

        Runs Ledger.run_query, to create a subprocess that runs: `ledger csv
        --related <acc_name>`.
        """
        ret = self.ledger.run_query(["csv", "--related", self.acc_name])
        for line in csv.reader(ret.splitlines()):
            payee, dst_account = line[2:4]
            self._payees[payee].append(dst_account)

    def get_account_by_payee(self, payee: str) -> str:
        """Get the most probable payee name via frequency.

        Cache holds a dictionary mapping payee names to a list of account
        names that have been on the same transaction with the source account.
        If payee name found on this cache, the most frequent account name on
        the list would be returned. If not a placeholder would be returned
        instead.

        Args:
            payee: String consisting payee name that would be checked for
            cached candidates.

        Returns:
            Most probable account name, or a placeholder in case of cache
            miss.

        """
        if payee in self._payees.keys():
            return Counter(self._payees[payee]).most_common(1)[0][0]
        return "Expenses:Misc"

    def get_identifier(self, row: dict) -> str:
        """Calculate the md5 hash sum of the given row.

        Sorts dictionary before writing updating hash object with each element.
        Also encodes each dictionary element to utf-8 for consistency.

        Args:
            row: Dictionary object for the row being processed.

        Returns:
            A string consisting the hash calculated.

        """
        h = hashlib.md5()
        for key in sorted(row.keys()):
            h.update((f"{key}={row[key]}\n").encode("utf-8"))
        return h.hexdigest()

    def is_row_synced(self, row: dict) -> bool:
        """Check whether the given row is in already synchronized id list.

        Args:
            row: Dictionary object for the row being processed.

        Returns:
            True if row is already synchronized, False otherwise.

        """
        return self.get_identifier(row) in self._synced_ids

    def skip_row(self, row: dict) -> bool:
        """Skip processing row if it is empty.

        Args:
            row: Dictionary object for the row being processed.

        Returns:
            A boolean for whether row should be skipped.

        """
        return row is None

    @abstractmethod
    def convert(self, row: dict) -> Transaction:
        """Convert given export row to a Transaction object.

        Args:
            row: Dictionary of the row to be processed.

        Returns:
            Resulting Transaction instance.

        """
        pass

    def make_currency(self, currency: str) -> str:
        """Convert if currency symbol to currency code, else return as is.

        Args:
            currency: String to be converted.

        Returns:
            Converted string.

        """
        if currency in self.CURRENCY_CODES.keys():
            return self.CURRENCY_CODES[currency]
        return currency

    @staticmethod
    def format_eu_number_to_us(numeric_str: str) -> str:
        """Convert a European-formatted numeric string to US standard format.

        Replaces thousands separators (dots) with nothing and the decimal
        separator (comma) with a dot (e.g., '1.234,56' -> '1234.56').

        Args:
            numeric_str: The European number string to reformat.

        Returns:
            The reformatted numeric string.

        """
        return numeric_str.replace(".", "").replace(",", ".")
