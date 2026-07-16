import logging
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
from pandas.core.groupby import DataFrameGroupBy

DOMAIN = "parsers"


class Parser(ABC):
    """Abstract base class for all parsers.

    Attributes:
        TYPE (str | None): Unique string identifier for the parser.
            Must be set by subclasses.
    """

    TYPE: str | None = None

    @abstractmethod
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a file and return a DataFrame.

        Args:
            fpath (Path): Path to the input file.

        Returns:
            pd.DataFrame: Parsed data with a 'dt' datetime column.
        """
        pass

    def groups(self, df: pd.DataFrame) -> DataFrameGroupBy:
        """Split a DataFrame into monthly groups.

        Args:
            df (pd.DataFrame): Full DataFrame with a 'dt' datetime column.

        Returns:
            DataFrameGroupBy: Grouped by month end frequency.
        """
        return df.groupby(pd.Grouper(key="dt", freq="ME"))

    def write_group(self, group: pd.DataFrame) -> None:
        """Write a group (i.e. month) to its destination.

        Preprocesses the group, drops the 'dt' column, and writes the
        result to a CSV file named after the group's month and the
        parser's TYPE.

        Args:
            group (pd.DataFrame): A slice of the full DataFrame,
                corresponding to a single month.
        """
        dt = group["dt"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"{dt}-{self.TYPE}.csv"
        group = self.preprocess_groups(group)
        group.drop("dt", axis=1).to_csv(fname, index=False)
        logging.info(f"Wrote {fname} to disk on cwd.")

    def preprocess_groups(self, group: pd.DataFrame) -> pd.DataFrame:
        """Preprocess a group before writing, i.e. sorting.

        Subclasses may override this to apply custom transformations
        (e.g. sorting rows, renaming columns) prior to writing the
        group to disk. Default implementation is a no-op.

        Args:
            group (pd.DataFrame): A slice of the full DataFrame.

        Returns:
            pd.DataFrame: The preprocessed group.
        """
        return group

    def parse(self, fpath: str) -> None:
        """Read a file and write all non-empty groups.

        Args:
            fpath (str): Path to the input file.
        """
        df = self.read_file(Path(fpath))
        logging.info(f"Read {fpath} from disk.")
        for _, group in self.groups(df):
            if not group.empty:
                self.write_group(group)
