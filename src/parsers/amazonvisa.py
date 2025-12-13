#!/usr/bin/env python

import pandas as pd

from parsers import Parser


class AmazonParser(Parser):
    TYPE = "amazon"

    def read_file(self, fpath):
        df = pd.read_excel(fpath, header=10).dropna(how="all")
        df["dt"] = pd.to_datetime(
            df["Datum"] + " " + df["Zeit"], format="%d.%m.%Y %H:%M Uhr"
        )
        return df

    def groups(self, df):
        return df.groupby(pd.Grouper(key="dt", freq="ME"))

    def parse_groups(self, month):
        dt = month["dt"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"out/{dt}-amazonvisa.csv"
        month = month.drop("dt", axis=1).to_csv(fname, index=False)
