import codecs
import csv

from ledger_jester.converter import CsvConverter


class CsvSynchronizer:
    def __init__(self, lgr, payee_format=None, date_format=None):
        self.lgr = lgr
        self.payee_format = payee_format
        self.date_format = date_format

    def is_row_synced(self, converter, row):
        if self.lgr is None:
            # User called with --no-ledger
            # All transactions are considered "synced" in this case.
            return False
        else:
            return self.lgr.check_transaction_by_id(
                "csvid", converter.get_csv_id(row)
            )

    def parse_file(self, path, accountname=None, unknownaccount=None):
        with open(path) as f:
            has_bom = f.read(3) == codecs.BOM_UTF8
            if not (has_bom):
                f.seek(0)
            else:
                f.seek(3)
            dialect = csv.Sniffer().sniff(f.readline())
            if not (has_bom):
                f.seek(0)
            else:
                f.seek(3)
            dialect.skipinitialspace = True
            reader = csv.DictReader(f, dialect=dialect)
            converter = CsvConverter.make_converter(
                set(reader.fieldnames),
                dialect,
                ledger=self.lgr,
                name=accountname,
                unknownaccount=unknownaccount,
                payee_format=self.payee_format,
                date_format=self.date_format,
            )
            # Create a new reader in case the converter modified the dialect
            if not (has_bom):
                f.seek(0)
            else:
                f.seek(3)
            reader = csv.DictReader(f, dialect=dialect)
            return [
                converter.convert(row)
                for row in reader
                if not self.is_row_synced(converter, row)
            ]
