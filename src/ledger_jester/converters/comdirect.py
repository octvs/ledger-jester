import logging
import re
from datetime import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

from ledger_jester.converter import (
    Amount,
    Converter,
    CsvConverter,
    Posting,
    Transaction,
)


class ComdirectConverter(CsvConverter):
    COLS = {
        "_": "Vorgang",
        "date0": "Buchungstag",
        "date1": "Wertstellung (Valuta)",
        "payee": "Buchungstext",
        "amount": "Umsatz in EUR",
    }
    DATE_FORMAT = "%d.%m.%Y"
    FIELDSET = set(COLS.values())
    REF_RE = re.compile(r"\s*Ref\.\s(\S+)")

    def __init__(self, *args, **kwargs):
        super(ComdirectConverter, self).__init__(*args, **kwargs)
        self.cols = SimpleNamespace(**self.COLS)
        if self.name is None:
            self.name = "Assets:Bank:Comdirect:Checking"
        # This can be later improved, I don't want to add a new cli flag now
        self.acc_type = "Current"
        if self.name.split(":")[-1] == "Savings":
            self.acc_type = "Deposit"

    def get_csv_id(self, row):
        match = self.REF_RE.search(row[self.cols.payee])
        if match:
            return "comdirect.%s" % (Converter.clean_id(match.group(1)))
        else:
            return CsvConverter.get_csv_id(self, row)

    @staticmethod
    def extract_pattern(text, reg):
        match = reg.search(text)
        if not match:
            return text, None
        text = text[: match.start()] + text[match.end() :]
        logging.debug(f"Found: {match.group(1)}")
        return text, match.group(1)

    def parse_comdirect_description(self, text):
        logging.debug(f"START: {text}")
        SENT_RE = re.compile(r"^\s*Empfänger:\s(.+?)(?=Kto/IBAN:)")
        IBAN_RE = re.compile(r"^Kto\/IBAN:\s(\w+)\s")
        BIC_RE = re.compile(r"^BLZ\/BIC:\s(\w+)")
        DEPOSIT_RE = re.compile(r"\s*(BARGELDEINZAHLUNG)")
        RECEIVED_RE = re.compile(
            r"^\s*Auftraggeber:\s(.+?)\s*(?=Buchungstext:|$)"
        )
        BOOKING_TEXT_RE = re.compile(r"\s*Buchungstext:\s(.*)$")
        CARD_TEXT_RE = re.compile(
            r"\s*(Kartenzahlung\scomdirect\sVisa-Debitkarte).*$"
        )
        FEE_RE = re.compile(r"\s*(Kontoführungsentgelt\sGirokonto)")
        text, _ = self.extract_pattern(text, self.REF_RE)  # Remove ref
        text, payee = self.extract_pattern(text, SENT_RE)
        if not payee:  # If not sent maybe received
            text, payee = self.extract_pattern(text, RECEIVED_RE)
        if not payee:  # If not a deposit
            text, payee = self.extract_pattern(text, DEPOSIT_RE)
        if not payee:  # Then a card payment
            text, payee = self.extract_pattern(text, CARD_TEXT_RE)
        if not payee:  # Then a fee
            text, payee = self.extract_pattern(text, FEE_RE)

        text, details = self.extract_pattern(text, IBAN_RE)
        if details:  # If found IBAN check for BIC
            text, _details = self.extract_pattern(text, BIC_RE)
            details = details + " - " + _details
        else:  # Generic details
            text, details = self.extract_pattern(text, BOOKING_TEXT_RE)
        logging.debug(f"LEFTOVER: {text}")

        return payee, details

    def convert(self, row):
        if self.skip_row(row):
            return None

        payee, details = self.parse_comdirect_description(row[self.cols.payee])

        date_start = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        date_comp = dt.strptime(row[self.cols.date1], self.DATE_FORMAT)
        amount = Decimal(self.eu_decimal_to_us(row[self.cols.amount]))
        currency = "EUR"
        cleared = True
        meta = {"csvid": self.get_csv_id(row)}
        if details:
            meta["details"] = details

        if date_start.date() == date_comp.date():
            date_comp = None

        # payee = self.filter_payee_names(row[self.cols.payee])
        # payee = self.lgr.get_autosync_payee(payee, self.name)

        acct_src = self.name
        acct_dst = self.mk_dynamic_account(payee, exclude=acct_src)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, reverse=True),
        )
        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount, currency),
            metadata=meta,
        )
        postings = [posting_dst, posting_src]

        if not acct_dst:
            postings = postings[1:]

        return Transaction(
            date=date_start,
            cleared=cleared,
            aux_date=date_comp,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
