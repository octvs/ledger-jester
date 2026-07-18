"""Parser for Revolut CSV exports."""

from pathlib import Path

import pandas as pd

from parsers.parser import DOMAIN, Parser
from registry import register


@register(DOMAIN)
class RevolutParser(Parser):
    """Parser for Revolut CSV exports."""

    TYPE = "revolut"
    FTYPE = "csv"

    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Revolut CSV export and return a DataFrame.

        Args:
            fpath (Path): Path to the input CSV file.

        Returns:
            pd.DataFrame: Parsed data with a 'dt' datetime column.

        Raises:
            ValueError: If the file is not a .csv file.

        """
        df = pd.read_csv(fpath)
        df["dt"] = pd.to_datetime(
            df["Completed Date"], format="%Y-%m-%d %H:%M:%S"
        )
        return df

    def preprocess_groups(self, group: pd.DataFrame) -> pd.DataFrame:
        """Sort a monthly group by completion date and product, stably.

        Args:
            group: A slice of the full DataFrame for a single month.

        Returns:
            pd.DataFrame: The group sorted by 'dt' then 'Product', with
            ties broken by original row order.

        """
        return group.sort_values(by=["dt", "Product"], kind="stable")
