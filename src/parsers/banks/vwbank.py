"""Parser for Volkswagen Bank CSV exports."""

from pathlib import Path
from typing import override

import pandas as pd

from parsers import REGISTRY, Parser


@REGISTRY.register
class VWBankParser(Parser):
    """Parser class for Volkswagen Bank CSV exports."""

    TYPE = "vwbank"
    FTYPE = "csv"

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a VW Bank CSV export and return a DataFrame."""
        df = pd.read_csv(fpath, header=6, sep=";")
        df = df.dropna(how="all", axis=1)
        df = df.drop("Nr.", axis=1)
        df["dt"] = pd.to_datetime(df["Buchungsdatum"], format="%d.%m.%Y")
        return df
