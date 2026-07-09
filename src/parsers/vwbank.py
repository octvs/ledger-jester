#!/usr/bin/env python

import pandas as pd

from parsers import Parser


class VWBankParser(Parser):
    TYPE = "vwbank"

    def read_file(self, fpath):
        if fpath.suffix != ".csv":
            print(f"Unsupported file extension provided: {fpath.suffix}")
            exit()
        df = pd.read_csv(fpath, header=6, sep=";")
        df = df.dropna(how="all", axis=1)
        df["Soll (EUR)"] = "-" + df["Soll (EUR)"]
        df["Umsatz"] = df["Haben (EUR)"].fillna("") + df["Soll (EUR)"].fillna(
            ""
        )
        df = df.drop(["Nr.", "Soll (EUR)", "Haben (EUR)"], axis=1)
        df["dt"] = pd.to_datetime(df["Wertstellung"], format="%d.%m.%Y")
        return df

    def groups(self, df):
        return df.groupby(pd.Grouper(key="dt", freq="ME"))

    def write_group(self, group):
        dt = group["dt"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"{dt}-{self.TYPE}.csv"
        group.drop("dt", axis=1).to_csv(fname, index=False)
