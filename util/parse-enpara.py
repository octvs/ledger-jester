#!/usr/bin/env nix
#! nix shell github:tomberek/-#python3With.pandas --command python

import sys
from pathlib import Path

import pandas as pd

fpath = Path(sys.argv[1])
if fpath.suffix != ".csv":
    print(
        f"Unsupported file extension provided: {fpath.suffix}\n"
        + "xls parsing is not supported due to format and encoding of the enpara export.\n"
        + "First export the necessary table to csv (i.e. via libreoffice)."
    )
    exit()


df = pd.read_csv(fpath).dropna(how="all")
df["dt"] = pd.to_datetime(df["Tarih"], format="%d.%m.%Y")
for _, month in df.groupby(pd.Grouper(key="dt", freq="ME")):
    dt = month["dt"].reset_index(drop=True)[0].strftime("%Y%m")
    fname = f"{dt}-enpara.csv"
    month = month.drop("dt", axis=1).to_csv(fname, index=False)
