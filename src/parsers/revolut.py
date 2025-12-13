#!/usr/bin/env python

import pandas as pd

from parsers import Parser


class RevolutParser(Parser):
    TYPE = "revolut"

    def read_file(self, fpath):
        if fpath.suffix != ".csv":
            print(f"Unsupported file extension provided: {fpath.suffix}")
            exit()
        df = pd.read_csv(fpath)
        df["dt"] = pd.to_datetime(
            df["Completed Date"], format="%Y-%m-%d %H:%M:%S"
        )
        return df

    def groups(self, df):
        return df.groupby(pd.Grouper(key="dt", freq="ME"))

    def parse_groups(self, month):
        dt = month["dt"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"out/{dt}-{self.TYPE}.csv"
        month = month.sort_values(by=["Completed Date", "Product"])
        month = month.drop("dt", axis=1).to_csv(fname, index=False)
