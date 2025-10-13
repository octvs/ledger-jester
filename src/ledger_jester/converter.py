import datetime
import hashlib
import re
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
            65 - indent - len(self.account) - len(self.amount.format())
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


class CsvConverter(Converter):
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

    def mk_currency(self, currency):
        if currency == "USD":
            currency = "$"
        elif currency == "GBP":
            currency = "£"
        elif currency == "EUR":
            currency = "€"
        return currency

    def convert(self, row):
        amt = Decimal(row["Amount"])
        if not amt:
            return ""
        currency = self.mk_currency(row["Currency"])
        cleared = row["State"] == "COMPLETED"
        if row["Type"] == "TOPUP":
            reverse = True
            acct_from = "Assets:Other"
            amt_from = Amount(amt, currency, reverse=reverse)
            acct_to = self.name
            amt_to = Amount(amt, currency, reverse=not reverse)
        else:
            reverse = False
            acct_from = self.name
            amt_from = Amount(amt, currency, reverse=reverse)
            acct_to = "Expenses:Misc"
            amt_to = Amount(amt, currency, reverse=not reverse)

        payee = row["Description"]
        meta = {"csvid": self.get_csv_id(row)}

        posting_from = Posting(
            acct_from,
            amt_from,
            metadata=meta if acct_from == self.name else {},
        )
        posting_fee = (
            Posting(
                "Expenses:Bank Charges",
                Amount(Decimal(row["Fee"]), currency, reverse=True),
            )
            if row["Fee"] != "0.00"
            else None
        )
        posting_to = Posting(
            acct_to, amt_to, metadata=meta if acct_to == self.name else {}
        )

        date = datetime.datetime.strptime(
            row["Started Date"], "%Y-%m-%d %H:%M:%S"
        )
        aux_date = (
            datetime.datetime.strptime(
                row["Completed Date"], "%Y-%m-%d %H:%M:%S"
            )
            if row["Completed Date"]
            else None
        )
        if aux_date and (date.date() == aux_date.date()):
            aux_date = None

        postings = [posting_to, posting_from]
        if posting_fee:
            postings.append(posting_fee)
            postings.append(posting_fee.clone_inverted(self.name))
        return Transaction(
            date=date,
            cleared=cleared,
            aux_date=aux_date,
            date_format="%Y-%m-%d",
            payee=payee,
            postings=postings,
        )
