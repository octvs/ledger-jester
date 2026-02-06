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
        # Clean
        df = df.dropna(how="all", axis=1)  # useless cols
        df = df.drop("Nr.", axis=1)  # useless index
        df["dt"] = pd.to_datetime(df["Buchungsdatum"], format="%d.%m.%Y")
        return df

    def groups(self, df):
        return df.groupby(pd.Grouper(key="dt", freq="ME"))

    def parse_groups(self, month):
        dt = month["dt"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"{dt}-{self.TYPE}.csv"
        month = month.drop("dt", axis=1).to_csv(fname, index=False)
