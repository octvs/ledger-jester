#!/usr/bin/env nix
#! nix shell github:tomberek/-#python3With.pandas nixpkgs#xan --command python

import subprocess
import sys
from pathlib import Path

import pandas as pd

fpath = Path(sys.argv[1])
if fpath.suffix == ".xls":
    _fpath = fpath.with_suffix(".csv")
    subprocess.run([f"xan from {fpath} | tail +10 >{_fpath}"], shell=True)
    fpath = _fpath
elif fpath.suffix != ".csv":
    print(f"Unsupported file extension provided: {fpath.suffix}")
    exit()

df = pd.read_csv(fpath).dropna(how="all")
df["dt"] = pd.to_datetime(
    df["Datum"] + " " + df["Zeit"], format="%d.%m.%Y %H:%M Uhr"
)
for _, month in df.groupby(pd.Grouper(key="dt", freq="ME")):
    dt = month["dt"].reset_index(drop=True)[0].strftime("%Y%m")
    fname = f"out/{dt}-amazonvisa.csv"
    month = month.drop("dt", axis=1).to_csv(fname, index=False)
