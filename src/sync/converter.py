"""Base converter implementation for csv statements."""


class CsvConverter:
    """Generic converter class for csv statements."""

    def skip_row(self, row: dict) -> bool:
        """Skip processing row if it is empty.

        Args:
            row: Dictionary object for the row being processed.

        Returns:
            A boolean for whether row should be skipped.

        """
        return row is None
