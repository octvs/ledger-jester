"""Base converter implementation for csv statements."""

from abc import ABC, abstractmethod

from ledger_wrapper import Transaction


class CsvConverter(ABC):
    """Generic converter class for csv statements."""

    COLS = {}

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
