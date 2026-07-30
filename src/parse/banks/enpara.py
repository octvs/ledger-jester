"""Parser for Enpara XLS exports."""

from io import BytesIO
from pathlib import Path
from typing import override

import pandas as pd

from parse import REGISTRY, Parser


@REGISTRY.register
class EnparaParser(Parser):
    """Parser class for Enpara XLS exports."""

    TYPE = "enpara"
    FTYPE = "xls"
    SUBTYPES = {"Vadesiz TL": "", "Birikim TL": "sav"}

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Enpara XLS export and return a DataFrame.

        Reverses DataFrame row order before returning to respect original
        reverse chronological order.

        """
        content = BytesIO(fpath.read_bytes())
        meta_df = pd.read_excel(content, header=None, nrows=3, usecols=[4])
        self.assign_subtype_suffix(meta_df.iat[2, 0])
        df = pd.read_excel(
            content, header=10, usecols=[1, 2, 5, 7, 8], skipfooter=4
        )
        df["dt"] = pd.to_datetime(df["Tarih"], format="%d/%m/%Y")
        return df[::-1]
