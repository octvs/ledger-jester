#!/usr/bin/env python

import pandas as pd

from parsers import Parser


class EnparaParser(Parser):
    """
    Parser for enpara exported excel files.
    """

    TYPE = "enpara"

    def read_file(self, fpath) -> pd.DataFrame:
        df1 = pd.read_excel(
            fpath,
            header=10,
            usecols=[1, 2, 5, 7, 8],
            skipfooter=4,
            parse_dates=[0],
            date_format="%d.%m.%Y",
        )
        return df1.rename(columns={df1.columns[0]: "Tarih"}).iloc[::-1]

    def groups(self, df):
        return df.groupby(pd.Grouper(key="Tarih", freq="ME"))

    def parse_groups(self, group):
        dt = group["Tarih"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"out/{dt}-enpara.csv"
        group.to_csv(fname, index=False)
