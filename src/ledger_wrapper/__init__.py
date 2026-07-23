"""A custom python wrapper for ledger to use with ledger-jester."""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from subprocess import run

COL_WIDTH = 61
INDENT = 4


def _indented_line(_str: str) -> str:
    """Indent given string for the global indent level."""
    return f"{' ' * INDENT}{_str}\n"


class Ledger:
    """Ledger class for enclosing implemented wrapper functionality."""

    def __init__(self) -> None:
        """Initialize ledger class.

        Runs self.locate_ledger_file to populate self.fpath attribute.
        """
        self.fpath: Path = self.locate_ledger_file()

    @staticmethod
    def locate_ledger_file() -> Path:
        """Find ledger file on the host system via LEDGER_FILE env var.

        Raises:
            ValueError: If LEDGER_FILE env var is not defined.

        """
        _ledger_fpath = os.getenv("LEDGER_FILE")
        if not _ledger_fpath:
            raise ValueError("You must defined LEDGER_FILE env var!")
        return Path(_ledger_fpath)

    def run_query(self, query: list[str]) -> str:
        """Run ledger query as a subprocess on shell.

        Args:
            query: List of strings that will be concatenated into a full
            command to run.

        Returns:
            Response of the query as a string.

        """
        cmd = ["ledger", "-f", str(self.fpath)] + query
        logging.debug(f"Running on sh: {' '.join(cmd)}")
        ret = run(cmd, capture_output=True, text=True)
        ret.check_returncode()
        return ret.stdout

    def fetch_all_metadata(self, key: str) -> set:
        """Fetch all metadata values for given key from ledger.

        Args:
            key: The metadata key that would be queried.

        Returns:
            A set consisting values for the given key.

        """
        query = [
            "csv",
            "expr",
            f"has_meta('{key}')",
            "--format",
            f"%(meta('{key}'))\\n",
        ]
        return set(self.run_query(query).splitlines())


@dataclass
class Amount:
    """Dataclass to represent an amount from ledger."""

    number: str
    currency: str
    invert: bool = False

    def __post_init__(self) -> None:
        """Post initialization steps for Amount class.

        Sets the internal _number variable as a Decimal from self.number.
        Inverts the same variable if self.invert is True.
        """
        self._number = Decimal(self.number)
        if self.invert:
            self._number = self._number.copy_negate()

    def __str__(self) -> str:
        """Return string representation of an amount in ledger syntax."""
        if len(self.currency) == 1:  # If symbol write before, else after
            return f"{self.currency} + {self._number:.2f}"
        return f"{self._number:.2f} {self.currency}"

    def __sub__(self, other: Amount) -> Amount:
        """Substract an Amount instance from another.

        Args:
           other: The other Amount instance to substact.

        Returns:
            The resulting amount.

        Raises:
            ValueError: If currencies of both are not the same.

        """
        assert isinstance(other, Amount)
        if self.currency != other.currency:
            raise ValueError("Can't operate on diff currencies.")
        return Amount(str(self._number - other._number), self.currency)

    def __gt__(self, other: Amount | int) -> bool:
        """Compare value of an amount to another Amount or int.

        Args:
           other: The other Amount instance to compare.

        Returns:
            A boolean corresponding to the comparison, True if the left hand
            side was larger, False otherwise.

        """
        if isinstance(other, int):
            return self._number > other
        else:
            assert isinstance(other, Amount)
            return self._number > other._number


@dataclass
class Posting:
    """Dataclass to represent a posting from ledger."""

    account: str
    amount: Amount
    asserted: None | Amount = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return string representation of a posting in ledger syntax."""
        _width = COL_WIDTH - INDENT - len(str(self.amount))
        retval = f"{self.account:<{_width}}{self.amount}"
        retval += f" = {self.asserted}" if self.asserted else ""
        for _key in sorted(self.metadata.keys()):
            retval += f"\n; {_key}: {self.metadata[_key]}"
        return retval


@dataclass
class Transaction:
    """Dataclass to represent a transaction from ledger."""

    date: datetime
    payee: str
    postings: list[Posting]
    aux_date: None | datetime = None
    cleared: bool = False
    date_format: str = "%Y/%m/%d"
    metadata: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return string representation of a transaction in ledger syntax."""
        retval = self.date.strftime(self.date_format)
        retval += (
            ""
            if not self.aux_date
            else f"={self.aux_date.strftime(self.date_format)}"
        )
        retval += " * " if self.cleared else " "
        retval += self.payee + "\n"
        for _key in sorted(self.metadata.keys()):
            retval += _indented_line(f"; {_key}: {self.metadata[_key]}")
        for posting in self.postings:
            for line in str(posting).split("\n"):
                retval += _indented_line(line)
        return retval
