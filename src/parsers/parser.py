"""Abstract base class for bank export parsers."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
from pandas.core.groupby import DataFrameGroupBy


class Parser(ABC):
    """Abstract base class for all parsers.

    Attributes:
        TYPE (str | None): Unique string identifier for the parser.
            Must be set by subclasses.
        FTYPE (str | None): File extension supported for the parser.
            Must be set by subclasses.
        SUBTYPES (dict[str,str]): Subtype definitions for the account.
            Must be set by subclasses if the parser is required to support
            multiple sub-accounts.

    """

    TYPE: str | None = None
    FTYPE: str | None = None
    SUBTYPES: dict[str, str] = {}

    def __init__(self) -> None:
        """Initialize parser instance with a default empty suffix string."""
        self.suffix: str = ""

    def assert_path(self, fpath: str) -> Path:
        """Check whether the file provided is supported by the parser.

        Args:
            fpath: Path to the input file.

        """
        _fpath = Path(fpath)
        if _fpath.suffix != f".{self.FTYPE}":
            raise ValueError(f"Unsupported file extension: {_fpath.suffix}")
        if not _fpath.exists():
            raise FileNotFoundError(f"Path given does not exist: {fpath}")
        return _fpath

    @abstractmethod
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a file and return a DataFrame.

        Args:
            fpath: Path to the input file.

        Returns:
            pd.DataFrame: Parsed data with a 'dt' datetime column.

        """
        pass

    def groups(self, df: pd.DataFrame) -> DataFrameGroupBy:
        """Split a DataFrame into monthly groups.

        Args:
            df: Full DataFrame with a 'dt' datetime column.

        Returns:
            DataFrameGroupBy: Grouped by month end frequency.

        """
        return df.groupby(pd.Grouper(key="dt", freq="ME"))

    def write_group(self, group: pd.DataFrame) -> None:
        """Write a group (i.e. month) to its destination.

        Preprocesses the group, drops the 'dt' column, and writes the
        result to a CSV file named after the group's month and the
        parser's TYPE, followed by its suffix if specified.

        Args:
            group: A slice of the full DataFrame,
                corresponding to a single month.

        """
        dt = group["dt"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"{dt}-{self.TYPE}{self.suffix}.csv"
        group = self.preprocess_groups(group)
        group.drop("dt", axis=1).to_csv(fname, index=False)
        logging.info(f"Wrote {fname} to disk on cwd.")

    def preprocess_groups(self, group: pd.DataFrame) -> pd.DataFrame:
        """Preprocess a group before writing, i.e. sorting.

        Subclasses may override this to apply custom transformations
        (e.g. sorting rows, renaming columns) prior to writing the
        group to disk. Default implementation is a no-op.

        Args:
            group: A slice of the full DataFrame.

        Returns:
            pd.DataFrame: The preprocessed group.

        """
        return group

    def parse(self, fpath: str) -> None:
        """Read a file and write all non-empty groups.

        Args:
            fpath: Path to the input file.

        """
        _fpath = self.assert_path(fpath)
        df = self.read_file(_fpath)
        logging.info(f"Read {_fpath} from disk.")
        for _, group in self.groups(df):
            if not group.empty:
                self.write_group(group)

    def assign_subtype_suffix(self, acc_type: str) -> None:
        """Assign account fname suffix for subtype before writing file.

        Args:
            acc_type: String to be used to infer account subtype suffix.

        Raises:
            ValueError: If subtype is not defined on the SUBTYPES dict.

        """
        if acc_type not in self.SUBTYPES:
            raise ValueError(
                f"Account type: {acc_type} is not recognized, can't recover."
            )
        if self.SUBTYPES[acc_type]:
            self.suffix = self.SUBTYPES[acc_type]
            logging.debug(f"Assigned subtype suffix: {self.suffix}")
