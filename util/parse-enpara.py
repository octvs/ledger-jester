#!/usr/bin/env python

"""
Parser for enpara exported excel files.

The problem with enpara is that is provides separate exports for its savings
and checking account, but no complete timestamps, only dates. Therefore if you
want balance assertions to work, you should merge these logs appropriately.
This is done on this script via `criss_cross_dfs` function.
"""

import logging
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm


def read_enpara_excel(fpath: Path) -> pd.DataFrame:
    df1 = pd.read_excel(
        fpath,
        header=10,
        usecols=[3, 5, 8, 11, 13],
        skipfooter=4,
        parse_dates=[0],
        date_format="%d.%m.%Y",
    )
    return df1.rename(columns={df1.columns[0]: "Tarih"}).iloc[::-1]


def get_cross_xact(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["Hareket tipi"].str.contains("Transfer")].head(1)


def criss_cross_dfs(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    cross_xact = get_cross_xact(df1)
    if cross_xact.empty:  # If no cross xact return immediately
        return pd.concat([df1, df2])
    _df1 = df1.reset_index()
    _df2 = df2.reset_index()
    src_xact = get_cross_xact(_df1)
    amount = src_xact["İşlem Tutarı (TL)"].iloc[0]
    dst_xact = _df2[_df2.loc[:, "İşlem Tutarı (TL)"] == amount * -1]
    block0 = _df1.loc[: src_xact.index[0] - 1]
    block1 = _df2.loc[: dst_xact.index[0]]
    res = pd.concat([block0, block1, src_xact])
    block2 = _df1.loc[src_xact.index[0] + 1 :].set_index("index")
    block3 = _df2.loc[dst_xact.index[0] + 1 :].set_index("index")
    rest = criss_cross_dfs(block2, block3)  # Recurse for more cross xacts left
    return pd.concat([res, rest]).set_index("index")


def merge_dfs(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    span = [df1["Tarih"].min(), df1["Tarih"].max()]
    merged = pd.DataFrame()
    for i in tqdm(range((span[1] - span[0]).days + 1)):  # Iterate over days
        date = span[0] + pd.Timedelta(days=i)
        xacts1 = df1[df1["Tarih"] == date]
        xacts2 = df2[df2["Tarih"] == date]
        res = criss_cross_dfs(xacts1, xacts2)
        merged = pd.concat([merged, res])
    return merged


def main():
    df1 = read_enpara_excel(Path(sys.argv[1]))
    df1["Hesap"] = "Vadesiz"

    df2 = read_enpara_excel(Path(sys.argv[2]))
    df2["Hesap"] = "Birikim"

    df = merge_dfs(df2, df1)
    assert len(df) == len(df1) + len(df2)  # assert no xact was lost

    for _, month in df.groupby(pd.Grouper(key="Tarih", freq="ME")):
        dt = month["Tarih"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"out/{dt}-enpara.csv"
        month = month.to_csv(fname, index=False)


if __name__ == "__main__":
    main()
