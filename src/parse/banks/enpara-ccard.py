"""Parser for Enpara Credit Card PDF exports."""

import re
from collections.abc import Iterator
from pathlib import Path
from typing import override

import pandas as pd
import pdfplumber

from parse import REGISTRY, Parser


@REGISTRY.register
class EnparaCCParser(Parser):
    """Parser class for Enpara Credit Card PDF exports."""

    TYPE = "enparacc"
    FTYPE = "pdf"

    # Regex pattern: (dd/mm/yyyy)\s(Description)\s(- 1.000,00 TL)
    TRANSACTION_RE = re.compile(
        r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?\s*[\d\.]+,\d{2}\sTL)$"
    )
    COLUMNS = ("İşlem Tarihi", "Açıklama", "Tutar")

    @staticmethod
    def _lines_from_pdf(fpath: Path) -> Iterator[str]:
        """Iterate over lines read from a pdf via pdfplumber.

        Args:
            fpath (Path): Path to the target PDF file.

        Yields:
            str: A single line of text extracted from the PDF.

        """
        with pdfplumber.open(fpath) as pdf:
            for page in pdf.pages:
                if text := page.extract_text():
                    yield from text.splitlines()

    @override
    def read_file(self, fpath: Path) -> pd.DataFrame:
        """Read Enpara Credit Card PDF file and return a DataFrame."""
        records = []
        for line in self._lines_from_pdf(fpath):
            if match := self.TRANSACTION_RE.match(line.strip()):
                records.append(dict(zip(self.COLUMNS, match.groups())))

        df = pd.DataFrame(records)
        df["dt"] = pd.to_datetime(df["İşlem Tarihi"], format="%d/%m/%Y")
        return df
