#!/usr/bin/env python

"""
Parser for enpara exported excel files.
"""

import sys
from pathlib import Path

import pandas as pd


def read_enpara_excel(fpath: Path) -> pd.DataFrame:
    df1 = pd.read_excel(
        fpath,
        header=10,
        usecols=[1, 2, 5, 7, 8],
        skipfooter=4,
        parse_dates=[0],
        date_format="%d.%m.%Y",
    )
    return df1.rename(columns={df1.columns[0]: "Tarih"}).iloc[::-1]


def main():
    df = read_enpara_excel(Path(sys.argv[1]))

    for _, month in df.groupby(pd.Grouper(key="Tarih", freq="ME")):
        dt = month["Tarih"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"out/{dt}-enpara.csv"
        month = month.to_csv(fname, index=False)


if __name__ == "__main__":
    main()
