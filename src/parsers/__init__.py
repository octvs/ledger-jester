from abc import ABC, abstractmethod
from pathlib import Path


class Parser(ABC):
    TYPE = None

    @abstractmethod
    def read_file(self, fpath):
        pass

    @abstractmethod
    def parse_groups(self, group):
        pass

    @abstractmethod
    def groups(self, df):
        pass

    def parse(self, fpath):
        if not (out := Path("./out")).exists():
            out.mkdir()
        fpath = Path(fpath)
        df = self.read_file(fpath)
        for _, group in self.groups(df):
            self.parse_groups(group)


def parser_factory(name):
    from .revolut import RevolutParser

    for klass in Parser.__subclasses__():
        if klass.TYPE == name:
            return klass()
    # Found no class, bail
    raise Exception("Cannot determine parser type.")
