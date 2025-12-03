#!/usr/bin/env python

import sys
from pathlib import Path

import pandas as pd

fpath = Path(sys.argv[1])
if fpath.suffix != ".csv":
    print(f"Unsupported file extension provided: {fpath.suffix}")
    exit()

df = pd.read_csv(fpath)
df["dt"] = pd.to_datetime(df["Date"] + df["Time"], format="%d/%m/%Y%H:%M:%S")
for _, month in df.groupby(pd.Grouper(key="dt", freq="ME")):
    if month.empty:
        continue
    dt = month["dt"].reset_index(drop=True)[0].strftime("%Y%m")
    fname = f"{dt}-paypal.csv"
    if Path(fname).exists():
        print("File already exists!")
        exit()
    month = month.sort_values(by=["Date", "Time"])
    month = month.drop("dt", axis=1).to_csv(fname, index=False)
