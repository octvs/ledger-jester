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
        self.subtype = None
        self.separator = "."

    def deduce_account_type(self, fpath):
        df_slice = pd.read_excel(fpath, usecols=[1, 2, 4])
        acc_type = df_slice.iat[1, 2]
        self.separator = df_slice.iat[10, 0][2]
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
            date_format=self.separator.join(["%d", "%m", "%Y"]),
        )
        return df1.rename(columns={df1.columns[0]: "Tarih"}).iloc[::-1]

    def groups(self, df):
        return df.groupby(pd.Grouper(key="Tarih", freq="ME"))

    def write_group(self, group):
        dt = group["Tarih"].reset_index(drop=True)[0].strftime("%Y%m")
        fname = f"{dt}-enpara{self.subtype}.csv"
        group.to_csv(fname, index=False)
