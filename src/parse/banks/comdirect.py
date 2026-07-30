"""Parser for Comdirect CSV exports."""

import re
from io import StringIO
from pathlib import Path
from typing import override

import pandas as pd

from parse import REGISTRY, Parser


@REGISTRY.register
class ComdirectParser(Parser):
    """Parser class for Comdirect CSV exports."""

    TYPE = "comdirect"
    FTYPE = "csv"
    SUBTYPES = {"Girokonto": "", "Tagesgeld PLUS-Konto": "sav"}

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Comdirect CSV export and return a DataFrame."""
        lines = fpath.read_text(encoding="latin-1").splitlines()
        subtype_str = re.findall(r'Umsätze\s+([^"]+)', lines[1])[0]
        self.assign_subtype_suffix(subtype_str)
        df = pd.read_csv(StringIO("\n".join(lines[4:-3])), sep=";")
        df = df.dropna(how="all", axis=1)
        df["dt"] = pd.to_datetime(df["Buchungstag"], format="%d.%m.%Y")
        return df
