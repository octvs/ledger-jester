"""Parser for Cepteteb xls exports."""

import re
from io import StringIO
from pathlib import Path
from typing import override

import pandas as pd

from parsers import REGISTRY, Parser


@REGISTRY.register
class CeptetebParser(Parser):
    """Parser class for Cepteteb xls exports."""

    TYPE = "cepteteb"
    FTYPE = "xls"
    SUBTYPES = {"CEPTETEB TL": "", "CEPTETEB EUR": "eur"}

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Cepteteb xls export and return a DataFrame."""
        html = fpath.read_text(encoding="utf-8")
        # Remove the empty thead placeholder rows that break column inference
        html = re.sub(r"<thead.*?</thead>", "", html, flags=re.DOTALL)
        tables = pd.read_html(StringIO(html), thousands=".", decimal=",")
        self.assign_subtype_suffix(tables[2].iat[3, 1])
        df = tables[3].dropna(how="all", axis=0)
        df["Dekont"] = df["Dekont"].astype(int)
        df["dt"] = pd.to_datetime(
            df["Tarih"] + " " + df["Saat"], format="%d/%m/%Y %H:%M"
        )
        return df
