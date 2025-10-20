from datetime import datetime as dt
from decimal import Decimal

from ledger_jester.converter import (
    Amount,
    Converter,
    CsvConverter,
    Posting,
    Transaction,
)


class PaypalConverter(CsvConverter):
    FIELDSET = {
        "Currency",
        "Date",
        "Gross",
        "Item Title",
        "Name",
        "Net",
        "Status",
        "To Email Address",
        "Transaction ID",
        "Type",
    }

    def __init__(self, *args, **kwargs):
        super(PaypalConverter, self).__init__(*args, **kwargs)
        if self.payee_format is None:
            self.payee_format = "{Name} {To Email Address} {Item Title} ID: {Transaction ID}, {Type}"

    def get_csv_id(self, row):
        return "paypal.%s" % (Converter.clean_id(row["Transaction ID"]))

    def convert(self, row):
        if (
            (row["Status"] != "Completed")
            and (row["Status"] != "Refunded")
            and (row["Status"] != "Reversed")
        ) or (row["Type"] == "Shopping Cart Item"):
            return ""
        else:
            currency = row["Currency"]
            posting_metadata = {"csvid": self.get_csv_id(row)}
            net = Decimal(row["Net"].replace(",", ""))
            gross = Decimal(row["Gross"].replace(",", ""))

            if (
                row["Type"] == "Add Funds from a Bank Account"
                or row["Type"] == "Charge From Debit Card"
            ):
                posting = Posting(
                    self.name, Amount(net, currency), metadata=posting_metadata
                )
                postings = [posting, posting.clone_inverted("Transfer:Paypal")]
            else:
                posting = Posting(
                    self.name,
                    Amount(gross, currency),
                    metadata=posting_metadata,
                )
                postings = [
                    posting,
                    # TODO Our payees are breaking the payee search in
                    # mk_dynamic_account
                    # self.mk_dynamic_account(payee, exclude=self.name),
                    posting.clone_inverted("Expenses:Misc"),
                ]
            return Transaction(
                date=dt.strptime(row["Date"], "%m/%d/%Y"),
                payee=self.format_payee(row),
                postings=postings,
                date_format=self.date_format,
            )
