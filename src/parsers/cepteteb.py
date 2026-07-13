#!/usr/bin/env python

import logging
import re
from io import StringIO

import pandas as pd

from parsers import Parser


class CeptetebParser(Parser):
    """
    Parser for cepteteb exported excel files.
    """

    TYPE = "cepteteb"

    def __init__(self):
        self.subtype = None

    def _read_file(self, fpath) -> str:
        with open(fpath) as f:
            html = f.read()
        # Remove the empty thead placeholder rows that break column inference
        return re.sub(r"<thead.*?</thead>", "", html, flags=re.DOTALL)

    def deduce_account_type(self, fpath):
        html = self._read_file(fpath)
        tables = pd.read_html(StringIO(html), thousands=".", decimal=",")
        acc_type = tables[2].iat[3, 1]
        if acc_type == "CEPTETEB TL":
            self.subtype = ""
        elif acc_type == "CEPTETEB EUR":
            self.subtype = "eur"
        else:
            logging.warning(
                f"Found {acc_type} on cell for account type, which is not recognized, can't recover."
            )
            exit()

    def read_file(self, fpath) -> pd.DataFrame:
        self.deduce_account_type(fpath)
        html = self._read_file(fpath)
        df = pd.read_html(StringIO(html), thousands=".", decimal=",")[3]
        df = df.dropna(how="all", axis=0)
        df["Tarih"] = pd.to_datetime(df["Tarih"], format="%d/%m/%Y")
        df["Valör"] = pd.to_datetime(df["Valör"], format="%d/%m/%Y")
        df["Dekont"] = df["Dekont"].astype(int)
        return (
            df.sort_values(["Tarih", "Saat"])
            .drop(columns="Saat")
            .reset_index(drop=True)
        )

    def groups(self, df):
        return df.groupby(pd.Grouper(key="Tarih", freq="ME"))

    def write_group(self, group):
        dt = group["Valör"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"{dt}-{self.TYPE}{self.subtype}.csv"
        group.to_csv(fname, index=False)
