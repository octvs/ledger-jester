from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd


class Parser(ABC):
    TYPE = None

    @abstractmethod
    def read_file(self, fpath):
        pass

    @abstractmethod
    def write_group(self, group):
        pass

    def groups(self, df):
        return df.groupby(pd.Grouper(key="dt", freq="ME"))

    def parse(self, fpath):
        df = self.read_file(Path(fpath))
        for _, group in self.groups(df):
            if not group.empty:
                self.write_group(group)


def parser_factory(name):
    from .amazonvisa import AmazonParser
    from .cepteteb import CeptetebParser
    from .comdirect import ComdirectParser
    from .enpara import EnparaParser
    from .paypal import PaypalParser
    from .revolut import RevolutParser
    from .vwbank import VWBankParser

    for klass in Parser.__subclasses__():
        if klass.TYPE == name:
            return klass()
    # Found no class, bail
    raise Exception("Cannot determine parser type.")
