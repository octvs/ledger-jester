import re
from datetime import datetime as dt
from decimal import Decimal
from types import SimpleNamespace

from ledger_jester.converter import Amount, CsvConverter, Posting, Transaction


class EnparaConverter(CsvConverter):
    # TODO: We can generalize with the following changes whole converters can
    # be squished mostly to the parent class most of the convert function gets
    # streamlind this way
    # TODO: Balance assertiosn
    COLS = {
        "amount": "İşlem Tutarı (TL)",
        "balance": "Bakiye (TL)",
        "date0": "Tarih",
        "payee": "Açıklama",
    }
    DATE_FORMAT = "%Y-%m-%d"
    FIELDSET = set(COLS.values())

    def __init__(self, *args, **kwargs):
        super(EnparaConverter, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = "Assets:Bank:Enpara"
        self.cols = SimpleNamespace(**self.COLS)

    def filter_payee_names(self, payee: str) -> str:
        payee = payee.split(",")[0]
        _prefixes = re.compile(r"\%\S* kampanyalı faiz oranı ile 1 g")
        return re.sub(_prefixes, "G", payee)

    def convert(self, row):
        if row is None:
            return None

        currency = "TRY"
        date_start = dt.strptime(row[self.cols.date0], self.DATE_FORMAT)
        amount = Decimal(row[self.cols.amount].replace(",", ""))
        posterior_bal = Decimal(row[self.cols.balance].replace(",", ""))
        meta = {"csvid": self.get_csv_id(row)}

        payee = self.filter_payee_names(row[self.cols.payee])
        payee = self.lgr.get_autosync_payee(payee, self.name)

        if row["Hesap"] == "Birikim":
            acct_src = self.name + ":Savings"
            if (
                "Transfer" in row["Hareket tipi"]
            ):  # Cross xact, use as bal assertion
                amount = Decimal("0.0")
                acct_dst = None
            else:
                acct_dst = self.mk_dynamic_account(payee, exclude=acct_src)
        else:
            acct_src = self.name + ":Checking"
            acct_dst = self.mk_dynamic_account(payee, exclude=acct_src)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, reverse=True),
        )
        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount, currency),
            asserted=Amount(posterior_bal, currency),
            metadata=meta,
        )
        postings = [posting_dst, posting_src]

        if not acct_dst:
            postings = postings[1:]

        return Transaction(
            date=date_start,
            cleared=True,
            aux_date=None,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )
