"""TODO."""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from subprocess import run

COL_WIDTH = 61
INDENT = 4


def _indented_line(_str):
    """TODO."""
    return f"{' ' * INDENT}{_str}\n"


class Ledger:
    """TODO."""

    def __init__(self):
        """TODO."""
        self.fpath: Path = self.locate_ledger_file()

    @staticmethod
    def locate_ledger_file():
        """TODO."""
        _ledger_fpath = os.getenv("LEDGER_FILE")
        if not _ledger_fpath:
            raise ValueError("You must defined LEDGER_FILE env var!")
        return Path(_ledger_fpath)

    def run_query(self, query):
        """TODO."""
        cmd = ["ledger", "-f", str(self.fpath)] + query
        logging.debug(f"Running on sh: {' '.join(cmd)}")
        ret = run(cmd, capture_output=True, text=True)
        ret.check_returncode()
        return ret.stdout


@dataclass
class Amount:
    """TODO."""

    number: str
    currency: str
    invert: bool = False

    def __post_init__(self):
        """TODO."""
        self._number = Decimal(self.number)
        if self.invert:
            self._number = self._number.copy_negate()

    def __str__(self):
        """TODO."""
        # If currency is symbol write before, else after
        if len(self.currency) == 1:
            return self.currency + str(self._number)
        return str(self._number) + " " + self.currency

    def __sub__(self, other):
        """TODO."""
        if isinstance(other, Amount):
            if self.currency != other.currency:
                return ValueError(
                    "Subtraction of diff currencies is not supported."
                )
            return Amount(self._number - other._number, self.currency)
        else:
            return NotImplemented

    def __gt__(self, other):
        """TODO."""
        if isinstance(other, Amount):
            return self._number > other._number
        elif isinstance(other, int):
            return self._number > other
        else:
            return NotImplemented


@dataclass
class Posting:
    """TODO."""

    account: str
    amount: Amount
    asserted: None | Amount = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __str__(self):
        """TODO."""
        retval = (
            f"{self.account:<{COL_WIDTH - len(str(self.amount))}}{self.amount}"
        )
        retval += f" = {self.asserted}" if self.asserted else ""
        for _key in sorted(self.metadata.keys()):
            retval += f"\n; {_key}: {self.metadata[_key]}"
        return retval


@dataclass
class Transaction:
    """TODO."""

    date: datetime
    payee: str
    postings: list[Posting]
    aux_date: None | datetime = None
    cleared: bool = False
    date_format: str = "%Y/%m/%d"
    metadata: dict[str, str] = field(default_factory=dict)

    def __str__(self):
        """TODO."""
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
