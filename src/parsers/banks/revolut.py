from pathlib import Path

import pandas as pd

from parsers.parser import Parser
from parsers.registry import register_parser


@register_parser
class RevolutParser(Parser):
    TYPE = "revolut"

    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Revolut CSV export and return a DataFrame.

        Args:
            fpath (Path): Path to the input CSV file.

        Returns:
            pd.DataFrame: Parsed data with a 'dt' datetime column.

        Raises:
            ValueError: If the file is not a .csv file.
        """
        if fpath.suffix != ".csv":
            raise ValueError(f"Unsupported file extension: {fpath.suffix}")
        df = pd.read_csv(fpath)
        df["dt"] = pd.to_datetime(
            df["Completed Date"], format="%Y-%m-%d %H:%M:%S"
        )
        return df

    def preprocess_groups(self, group: pd.DataFrame) -> pd.DataFrame:
        return group.sort_values(by=["dt", "Product"], kind="stable")
