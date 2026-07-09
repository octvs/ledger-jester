#!/usr/bin/env python

import logging

import pandas as pd

from parsers import Parser


class ComdirectParser(Parser):
    TYPE = "comdirect"

    def __init__(self):
        self.subtype = None
        self.encoding = "latin-1"

    def deduce_account_type(self, fpath):
        df_slice = pd.read_csv(fpath, nrows=0, encoding=self.encoding)
        acc_type = df_slice.columns[0].split(" ")[1].split(";")[0]
        if acc_type == "Girokonto":
            self.subtype = ""
        elif acc_type == "Tagesgeld":
            self.subtype = "sav"
        else:
            logging.warning(
                f"Found {acc_type} on cell for account type, which is not recognized, can't recover."
            )
            exit()

    def read_file(self, fpath):
        if fpath.suffix != ".csv":
            print(f"Unsupported file extension provided: {fpath.suffix}")
            exit()
        self.deduce_account_type(fpath)
        df = pd.read_csv(
            fpath,
            sep=";",
            skiprows=4,
            skipfooter=3,
            encoding=self.encoding,
            engine="python",
        )
        df = df.dropna(how="all", axis=1)
        df["dt"] = pd.to_datetime(
            df["Wertstellung (Valuta)"], format="%d.%m.%Y"
        )
        return df

    def groups(self, df):
        return df.groupby(pd.Grouper(key="dt", freq="ME"))

    def write_group(self, group):
        dt = group["dt"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"{dt}-{self.TYPE}{self.subtype}.csv"
        group.drop("dt", axis=1).to_csv(fname, index=False)
