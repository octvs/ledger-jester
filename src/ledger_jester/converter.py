import hashlib
import re
from csv import DictReader
from datetime import datetime as dt
from decimal import Decimal


class Transaction(object):
    def __init__(
        self,
        date,
        payee,
        postings,
        checknum=None,
        cleared=False,
        metadata={},
        aux_date=None,
        date_format=None,
    ):
        self.date = date
        self.aux_date = aux_date
        self.payee = payee
        self.postings = postings
        self.metadata = metadata
        self.cleared = cleared
        self.date_format = date_format
        self.checknum = checknum

    def format(self, indent=4, assertions=True):
        retval = ""
        cleared_str = " "
        checknum_str = ""
        if self.cleared:
            cleared_str = " * "
        aux_date_str = ""
        if self.date_format is None:
            self.date_format = "%Y/%m/%d"
        if self.aux_date is not None:
            aux_date_str = "=%s" % (self.aux_date.strftime(self.date_format))
        if self.checknum is not None:
            checknum_str = " (%d)" % (self.checknum)
        retval += "%s%s%s%s%s\n" % (
            self.date.strftime(self.date_format),
            checknum_str,
            aux_date_str,
            cleared_str,
            self.payee,
        )
        for k in sorted(self.metadata.keys()):
            retval += "%s; %s: %s\n" % (" " * indent, k, self.metadata[k])
        for posting in self.postings:
            retval += posting.format(indent, assertions)
        return retval


class Posting(object):
    def __init__(
        self, account, amount, asserted=None, unit_price=None, metadata={}
    ):
        self.account = account
        self.amount = amount
        self.asserted = asserted
        self.unit_price = unit_price
        self.metadata = metadata

    def format(self, indent=4, assertions=True):
        space_count = (
            61 - indent - len(self.account) - len(self.amount.format())
        )
        if space_count < 2:
            space_count = 2
        retval = "%s%s%s%s" % (
            " " * indent,
            self.account,
            " " * space_count,
            self.amount.format(),
        )
        if assertions and self.asserted is not None:
            retval = "%s = %s" % (retval, self.asserted.format())
        if self.unit_price is not None:
            retval = "%s @ %s" % (retval, self.unit_price.format())
        retval += "\n"
        for k in sorted(self.metadata.keys()):
            retval += "%s; %s: %s\n" % (" " * indent, k, self.metadata[k])
        return retval

    def clone_inverted(self, account, asserted=None, metadata={}):
        return Posting(
            account,
            self.amount.clone_inverted(),
            asserted=asserted,
            unit_price=self.unit_price,
            metadata=metadata,
        )


class Amount:
    def __init__(self, number, currency, reverse=False, unlimited=False):
        self.number = Decimal(number)
        self.reverse = reverse
        self.unlimited = unlimited
        self.currency = currency

    def format(self):
        # Commodities must be quoted in ledger if they have
        # whitespace or numerals.
        if re.search(r"[\s0-9]", self.currency):
            currency = '"%s"' % (self.currency)
        else:
            currency = self.currency
        if self.unlimited:
            number = str(abs(self.number))
        else:
            number = "%0.2f" % (abs(self.number))
        if self.number.is_signed() != self.reverse:
            prefix = "-"
        else:
            prefix = ""
        if len(currency) == 1:
            # $ comes before
            return "%s%s%s" % (prefix, currency, number)
        else:
            # USD comes after
            return "%s%s %s" % (prefix, number, currency)

    def clone_inverted(self):
        return Amount(
            self.number,
            self.currency,
            reverse=not (self.reverse),
            unlimited=self.unlimited,
        )

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Converter(object):
    def __init__(
        self,
        ledger=None,
        unknownaccount=None,
        currency="$",
        indent=4,
        payee_format=None,
        date_format=None,
        infer_account=True,
    ):
        self.lgr = ledger
        self.indent = indent
        self.unknownaccount = unknownaccount
        self.currency = currency.upper()
        self.payee_format = payee_format
        if self.currency == "USD":
            self.currency = "$"
        self.date_format = date_format
        self.infer_account = infer_account

    def mk_dynamic_account(self, payee, exclude):
        if self.lgr is None or not self.infer_account:
            return self.unknownaccount or "Expenses:Misc"
        else:
            account = self.lgr.get_account_by_payee(payee, exclude)
            if account is None:
                return self.unknownaccount or "Expenses:Misc"
            else:
                return account

    @staticmethod
    def clean_id(id):
        return (
            id.replace("/", "_")
            .replace("$", "_")
            .replace(" ", "_")
            .replace("@", "_")
            .replace("*", "_")
            .replace("+", "_")
            .replace("&", "_")
            .replace("[", "_")
            .replace("]", "_")
            .replace("|", "_")
            .replace("%", "_")
        )


class CsvConverter(Converter):
    def __init__(
        self,
        dialect,
        name=None,
        indent=4,
        ledger=None,
        unknownaccount=None,
        payee_format=None,
        date_format=None,
        infer_account=True,
    ):
        super(CsvConverter, self).__init__(
            ledger=ledger,
            indent=indent,
            unknownaccount=unknownaccount,
            payee_format=payee_format,
            date_format=date_format,
            infer_account=infer_account,
        )
        self.name = name
        self.dialect = dialect

    def preprocess(self, reader: DictReader) -> list[dict]:
        return list(reader)

    @staticmethod
    def make_converter(fieldset, dialect, name=None, **kwargs):
        for klass in CsvConverter.descendants():
            if klass.FIELDSET <= fieldset:
                return klass(dialect, name=name, **kwargs)
        # Found no class, bail
        raise Exception("Cannot determine CSV type")

    @classmethod
    def descendants(cls):
        retval = cls.__subclasses__()
        for cls2 in cls.__subclasses__():
            retval.extend(cls2.descendants())
        return retval

    # By default, return an MD5 of the key-value pairs in the row.
    # If a better ID is available, should be overridden.
    def get_csv_id(self, row):
        h = hashlib.md5()
        for key in sorted(row.keys()):
            h.update(("%s=%s\n" % (key, row[key])).encode("utf-8"))
        return h.hexdigest()

    def format_payee(self, row):
        return re.sub(r"\s+", " ", self.payee_format.format(**row).strip())


class RevolutConverter(CsvConverter):
    FIELDSET = set(
        [
            "Type",
            "Product",
            "Started Date",
            "Completed Date",
            "Description",
            "Amount",
            "Fee",
            "Currency",
            "State",
            "Balance",
        ]
    )

    def __init__(self, *args, **kwargs):
        super(RevolutConverter, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = "Assets:Bank:Revolut"

    def preprocess(self, reader: DictReader) -> list[dict]:
        """
        Preprocess logs to sort based on date and account type.

        The converter expects the cross postings between current and deposit
        account to be consequent. This is required for balance assertions for
        the latter to work.
        """
        return sorted(reader, key=lambda x: x["Completed Date"] + x["Product"])

    def convert(self, row):
        # Ignore reverted xacts
        if row is None or (row["State"] in ["REVERTED", "PENDING"]):
            return None

        date_start = dt.strptime(row["Started Date"], "%Y-%m-%d %H:%M:%S")
        date_comp = dt.strptime(row["Completed Date"], "%Y-%m-%d %H:%M:%S")
        amount = Decimal(row["Amount"])
        fee = Decimal(row["Fee"])
        currency = row["Currency"]
        cleared = row["State"] == "COMPLETED"
        posterior_bal = Decimal(row["Balance"])
        meta = {"csvid": self.get_csv_id(row)}

        if date_start.date() == date_comp.date():
            date_comp = None

        _prefixes = re.compile(r"(From |To |Payment from )")
        payee = re.sub(_prefixes, "", row["Description"])
        payee = self.lgr.get_autosync_payee(payee, self.name)

        if row["Product"] == "Deposit":
            acct_src = self.name + ":Savings"
            if row["Type"] == "Transfer":  # Cross xact, use as bal assertion
                amount = Decimal("0.0")
                acct_dst = None
            else:
                assert row["Type"] == "Interest"  # Rest is not implemented.
                acct_dst = "Income:Interest:Revolut"
        else:
            acct_src = self.name + ":Checking"
            acct_dst = self.mk_dynamic_account(payee, exclude=acct_src)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, reverse=True),
        )
        posting_src = Posting(
            account=acct_src,
            amount=Amount(amount - fee, currency),
            asserted=Amount(posterior_bal, currency),
            metadata=meta,
        )
        posting_fee = Posting(
            "Expenses:Finance:Revolut", Amount(fee, currency)
        )
        postings = [posting_dst, posting_src]

        if not acct_dst:
            postings = postings[1:]

        if fee > 0:
            postings.append(posting_fee)

        return Transaction(
            date=date_start,
            cleared=cleared,
            aux_date=date_comp,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )


class AmazonVisaConverter(CsvConverter):
    FIELDSET = set(
        [
            "Datum",
            "Zeit",
            "Karte",
            "Beschreibung",
            "Umsatzkategorie",
            "Unterkategorie",
            "Betrag",
            "Punkte",
        ]
    )

    def __init__(self, *args, **kwargs):
        super(AmazonVisaConverter, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = "Liabilities:CreditCard:Amazon"

    def get_csv_id(self, row: dict):
        """
        Get csv id for a row ignoring 'Punkte' column.

        Aforementioned column gets updated with a delay around 3-5 days with
        which we don't want to update our logs, hence ignore it for csvid.
        """
        # This later can be revoked in case we start handling the "Punkte" col
        _row = dict(row)
        del _row["Punkte"]
        return super(AmazonVisaConverter, self).get_csv_id(_row)

    def convert(self, row):
        if row is None:
            return None

        date = dt.strptime(row["Datum"], "%d.%m.%Y ")
        _amount, _curr = row["Betrag"].split()
        amount = Decimal(_amount.replace(",", "."))
        currency = self.mk_currency(_curr)
        meta = {"csvid": self.get_csv_id(row)}
        payee = self.lgr.get_autosync_payee(row["Beschreibung"], self.name)
        acct_dst = self.mk_dynamic_account(payee, exclude=self.name)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, reverse=True),
        )
        posting_src = Posting(
            account=self.name,
            amount=Amount(amount, currency),
            metadata=meta,
        )
        postings = [posting_dst, posting_src]

        return Transaction(
            date=date,
            cleared=True,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
        )

    @staticmethod
    def mk_currency(currency):
        if currency == "$":
            currency = "USD"
        elif currency == "£":
            currency = "GBP"
        elif currency == "€":
            currency = "EUR"
        return currency


class WalletConverter(CsvConverter):
    FIELDSET = set(["Date", "Payee", "Amount", "Currency", "Balance"])

    def __init__(self, *args, **kwargs):
        super(WalletConverter, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = "Assets:Cash:Wallet"
        self.date = None

    @staticmethod
    def mk_currency(currency):
        return "EUR" if currency == "" else currency

    def preprocess(self, reader: DictReader) -> list[dict]:
        """
        Preprocess logs to deduce date.

        Since csv logs for wallet are intended to be written by hand this
        converter allows user to abstain year and month parts of a date if it
        is same with the first row of the csv. For this purpose we set the
        class date variable ("%Y%m") from the first row.
        """
        _reader = list(reader)
        self.date = _reader[0]["Date"][:6]  # assuming %Y%m%d
        return _reader

    def mk_date(self, date):
        if len(date) == 2:
            date = self.date + date
        elif len(date) == 4:
            date = self.date[:4] + date
        return date

    def convert(self, row):
        if row is None:
            return None

        date = dt.strptime(self.mk_date(row["Date"]), "%Y%m%d")
        amount = Decimal(row["Amount"])
        currency = self.mk_currency(row["Currency"])
        bal = Decimal(row["Balance"]) if row["Balance"] != "" else None
        meta = {"csvid": self.get_csv_id(row)}
        payee = self.lgr.get_autosync_payee(row["Payee"], self.name)
        acct_dst = self.mk_dynamic_account(payee, exclude=self.name)

        posting_dst = Posting(
            account=acct_dst,
            amount=Amount(amount, currency, reverse=True),
        )
        posting_src = Posting(
            account=self.name,
            amount=Amount(amount, currency),
            asserted=Amount(bal, currency) if bal else None,
            metadata=meta,
        )

        postings = [posting_dst, posting_src]

        return Transaction(
            date=date,
            cleared=True,
            date_format="%Y/%m/%d",
            payee=payee,
            postings=postings,
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
