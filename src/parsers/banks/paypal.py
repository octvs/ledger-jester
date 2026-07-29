"""Parser for Paypal CSV exports."""

from pathlib import Path
from typing import override

import pandas as pd

from parsers import REGISTRY, Parser


@REGISTRY.register
class PaypalParser(Parser):
    """Parser class for Paypal CSV exports."""

    TYPE = "paypal"
    FTYPE = "csv"

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Paypal CSV export and return a DataFrame."""
        df = pd.read_csv(fpath)
        df["dt"] = pd.to_datetime(
            df["Date"] + " " + df["Time"], format="%d.%m.%Y %H:%M:%S"
        )
        return df
