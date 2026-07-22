"""Parser for Amazon Visa Excel exports."""

from pathlib import Path
from typing import override

import pandas as pd

from parsers import REGISTRY, Parser


@REGISTRY.register
class AmazonParser(Parser):
    """Parser class for Amazon Visa Excel (.xls) exports."""

    TYPE = "amazonvisa"
    FTYPE = "xls"

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Amazon Visa xls export and return a DataFrame."""
        df = pd.read_excel(fpath, header=10).dropna(how="all")
        df["dt"] = pd.to_datetime(
            df["Datum"] + " " + df["Zeit"], format="%d.%m.%Y %H:%M Uhr"
        )
        return df
