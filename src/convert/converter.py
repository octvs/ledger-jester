"""Base converter implementation for csv statements."""

import csv
import hashlib
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass, fields
from functools import cached_property
from typing import Generic, Self, TypeVar

from ledger_wrapper import Ledger, Transaction

CURRENCY_CODES: dict[str, str] = {
    "$": "USD",
    "£": "GBP",
    "€": "EUR",
    "₺": "TRY",
    "TL": "TRY",
}


@dataclass
class CsvRow(ABC):
    """Generic dataclass for csv statement rows."""

    @cached_property
    def csvid(self) -> str:
        """Compute the md5 sum on first access and cache the result."""
        field_values = tuple(
            getattr(self, field_name)
            for field_name, _ in self._get_csv_fields()
        )
        raw_repr = repr(field_values).encode("utf-8")
        return hashlib.md5(raw_repr).hexdigest()

    @classmethod
    def from_dict(cls, line: dict[str, str]) -> Self:
        """Map raw CSV keys to dataclass attributes.

        Args:
            line: CSV row to be converted to a CsvRow dataclass instance.

        Returns:
            Dataclass instance.

        """
        kwargs = {
            field_name: line[col_header]
            for field_name, col_header in cls._get_csv_fields()
        }
        return cls(**kwargs)

    @classmethod
    def _get_csv_fields(cls) -> list[tuple[str, str]]:
        """Return tuples of (dataclass_field_name, csv_column_header)."""
        return [
            (f.name, f.metadata["col"])
            for f in fields(cls)
            if "col" in f.metadata
        ]

    @classmethod
    def get_headers(cls) -> set[str]:
        """Extract all expected CSV headers from field metadata."""
        return {col_header for _, col_header in cls._get_csv_fields()}

    @staticmethod
    def make_currency(currency: str) -> str:
        """Convert if currency symbol to currency code, else return as is.

        Args:
            currency: String to be converted.

        Returns:
            Converted string.

        """
        if currency in CURRENCY_CODES.keys():
            return CURRENCY_CODES[currency]
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


RowT = TypeVar("RowT", bound=CsvRow)


class CsvConverter(ABC, Generic[RowT]):
    """Generic converter class for csv statements.

    Attributes:
        acc_name: The target account name associated with this converter instance.
        ledger: The Ledger wrapper instance used to query existing transactions.

    """

    ROW_TYPE: type[RowT]

    def __init__(self, account: str) -> None:
        """Initialize converter with the target account name.

        Loads related payees via self.fetch_related_accounts and
        already synchronized transaction IDs via Ledger.fetch_all_metadata.

        Args:
            account: The name of the target ledger account.

        """
        self.acc_name: str = account
        self.ledger: Ledger = Ledger()
        self._related_payees: dict[str, list[str]] = (
            self.fetch_related_accounts()
        )
        self._synced_ids: set[str] = self.ledger.fetch_all_metadata("csvid")

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Verify that converters explicitly define a ROW_TYPE attribute."""
        super().__init_subclass__(**kwargs)
        if "ROW_TYPE" not in cls.__dict__:
            raise TypeError(
                f"'{cls.__name__}' must explicitly declare a 'ROW_TYPE' attribute."
            )

    def fetch_related_accounts(self) -> dict:
        """Load all payee/account pairs related to the target account.

        Runs Ledger.run_query, to create a subprocess that runs: `ledger csv
        --related <acc_name>`.
        """
        _pairs = defaultdict(list)
        ret = self.ledger.run_query(["csv", "--related", self.acc_name])
        for line in csv.reader(ret.splitlines(), escapechar="\\"):
            _pairs[line[2]].append(line[3])
        return _pairs

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
        if payee in self._related_payees.keys():
            return Counter(self._related_payees[payee]).most_common(1)[0][0]
        return "Expenses:Misc"

    def is_row_synced(self, row: RowT) -> bool:
        """Check whether the given row is in already synchronized id list.

        Args:
            row: Dictionary object for the row being processed.

        Returns:
            True if row is already synchronized, False otherwise.

        """
        return row.csvid in self._synced_ids

    def skip_row(self, row: RowT) -> bool:
        """Skip processing row if it is empty.

        Args:
            row: Dictionary object for the row being processed.

        Returns:
            A boolean for whether row should be skipped.

        """
        return row is None

    @abstractmethod
    def convert(self, row: RowT) -> Transaction:
        """Convert given export row to a Transaction object.

        Args:
            row: Dictionary of the row to be processed.

        Returns:
            Resulting Transaction instance.

        """
        pass
