"""Parser for Revolut CSV exports."""

from pathlib import Path
from typing import override

import pandas as pd

from parsers import REGISTRY, Parser


@REGISTRY.register
class RevolutParser(Parser):
    """Parser class for Revolut CSV exports."""

    TYPE = "revolut"
    FTYPE = "csv"

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Revolut CSV export and return a DataFrame."""
        df = pd.read_csv(fpath)
        df["dt"] = pd.to_datetime(
            df["Completed Date"], format="%Y-%m-%d %H:%M:%S"
        )
        return df

    @override
    def preprocess_groups(self, group: pd.DataFrame) -> pd.DataFrame:
        """Sort a monthly group by completion date and product, stably."""
        return group.sort_values(by=["dt", "Product"], kind="stable")
