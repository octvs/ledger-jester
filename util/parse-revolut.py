#!/usr/bin/env nix
#! nix shell github:tomberek/-#python3With.pandas nixpkgs#xan --command python

import sys
from pathlib import Path

import pandas as pd

fpath = Path(sys.argv[1])
if fpath.suffix != ".csv":
    print(f"Unsupported file extension provided: {fpath.suffix}")
    exit()

df = pd.read_csv(fpath)
df["dt"] = pd.to_datetime(df["Completed Date"], format="%Y-%m-%d %H:%M:%S")
for _, month in df.groupby(pd.Grouper(key="dt", freq="ME")):
    dt = month["dt"].reset_index(drop=True)[0].strftime("%Y%m")
    fname = f"{dt}-revolut.csv"
    month = month.sort_values(by=["Completed Date", "Product"])
    month = month.drop("dt", axis=1).to_csv(fname, index=False)
