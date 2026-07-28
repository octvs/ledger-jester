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

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read a Cepteteb xls export and return a DataFrame."""
        html = fpath.read_text(encoding="utf-8")
        # Remove the empty thead placeholder rows that break column inference
        html = re.sub(r"<thead.*?</thead>", "", html, flags=re.DOTALL)
        tables = pd.read_html(StringIO(html), thousands=".", decimal=",")
        self.deduce_account_type(tables[2])
        df = tables[3].dropna(how="all", axis=0)
        df["Dekont"] = df["Dekont"].astype(int)
        df["dt"] = pd.to_datetime(
            df["Tarih"] + " " + df["Saat"], format="%d/%m/%Y %H:%M"
        )
        return df

    def deduce_account_type(self, table: pd.DataFrame) -> None:
        """Read and assign account subtype before processing file.

        Args:
            table: DataFrame containing account metadata key-value pairs.

        Raises:
            ValueError: If the account type in the table is unrecognized.

        """
        _acc_type = table.set_index(0)[1]["Hesap Türü"]
        if _acc_type == "CEPTETEB TL":
            self.subtype = ""
        elif _acc_type == "CEPTETEB EUR":
            self.subtype = "eur"
        else:
            raise ValueError(
                f"Found {_acc_type} on cell for account type, which is not recognized, can't recover."
            )
