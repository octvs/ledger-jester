"""Parser for Cepteteb xls exports."""

import re
from io import StringIO
from pathlib import Path
from typing import override

import pandas as pd

from parse import REGISTRY, Parser


@REGISTRY.register
class CeptetebParser(Parser):
    """Parser class for Cepteteb xls exports."""

    TYPE = "cepteteb"
    FTYPE = "xls"
    SUBTYPES = {"CEPTETEB TL": "", "CEPTETEB EUR": "eur"}

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Cepteteb xls export and return a DataFrame.

        Reverses DataFrame row order before returning to respect original
        reverse chronological order.

        """
        html = fpath.read_text(encoding="utf-8")
        # Remove the empty thead placeholder rows that break column inference
        html = re.sub(r"<thead.*?</thead>", "", html, flags=re.DOTALL)
        tables = pd.read_html(StringIO(html), thousands=".", decimal=",")
        self.assign_subtype_suffix(tables[2].iat[3, 1])
        df = tables[3].dropna(how="all", axis=0).copy()
        df["Dekont"] = df["Dekont"].astype(int)
        df["Kur"] = tables[2].iat[3, 1].split(" ")[1]
        df["dt"] = pd.to_datetime(
            df["Tarih"] + " " + df["Saat"], format="%d/%m/%Y %H:%M"
        )
        return df[::-1]
