#!/usr/bin/env python

import logging

import pandas as pd

from parsers import Parser


class EnparaParser(Parser):
    """
    Parser for enpara exported excel files.
    """

    TYPE = "enpara"

    def __init__(self):
        subtype = None

    def deduce_account_type(self, fpath):
        acc_type = pd.read_excel(fpath, usecols=[1, 4]).iat[1, 1]
        if acc_type == "Vadesiz TL":
            self.subtype = ""
        elif acc_type == "Birikim TL":
            self.subtype = "sav"
        else:
            logging.warning(
                f"Found {acc_type} on cell for account type, which is not recognized, can't recover."
            )
            exit()

    def read_file(self, fpath) -> pd.DataFrame:
        self.deduce_account_type(fpath)
        df1 = pd.read_excel(
            fpath,
            header=10,
            usecols=[1, 2, 5, 7, 8],
            skipfooter=4,
            parse_dates=[0],
            date_format="%d.%m.%Y",
        )
        return df1.rename(columns={df1.columns[0]: "Tarih"}).iloc[::-1]

    def groups(self, df):
        return df.groupby(pd.Grouper(key="Tarih", freq="ME"))

    def parse_groups(self, group):
        dt = group["Tarih"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"out/{dt}-enpara{self.subtype}.csv"
        group.to_csv(fname, index=False)
