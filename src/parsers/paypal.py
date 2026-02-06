#!/usr/bin/env python

import sys
from pathlib import Path

import pandas as pd

from parsers import Parser


class PaypalParser(Parser):
    TYPE = "paypal"

    def read_file(self, fpath):
        fpath = Path(sys.argv[1])
        if fpath.suffix != ".csv":
            print(f"Unsupported file extension provided: {fpath.suffix}")
            exit()

        df = pd.read_csv(fpath)
        df["dt"] = pd.to_datetime(
            df["Date"] + df["Time"], format="%d/%m/%Y%H:%M:%S"
        )
        return df

    def groups(self, df):
        return df.groupby(pd.Grouper(key="dt", freq="ME"))

    def write_group(self, group):
        if group.empty:
            return None
        dt = group["dt"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"{dt}-paypal.csv"
        if Path(fname).exists():
            print("File already exists!")
            exit()
        group = group.sort_values(by=["Date", "Time"])
        group = group.drop("dt", axis=1).to_csv(fname, index=False)
