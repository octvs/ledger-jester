import argparse
import logging
import os
import re
import sys
from pathlib import Path

from ledger_jester.ledgerwrap import Ledger
from ledger_jester.sync import CsvSynchronizer


def find_ledger_file():
    if "LEDGER_FILE" in os.environ:
        return Path(os.getenv("LEDGER_FILE")).expanduser().absolute()
    else:
        logging.warn("Please define LEDGER_FILE env var!")
        return None


def import_csv(ledger, args):
    if args.account is None:
        raise Exception(
            "When importing a CSV file, you must specify an account name."
        )
    sync = CsvSynchronizer(
        ledger, payee_format=args.payee_format, date_format=args.date_format
    )
    txns = sync.parse_file(
        args.fpath,
        accountname=args.account,
        unknownaccount=args.unknownaccount,
    )
    for txn in txns:
        if txn is not None:
            print(txn.format(args.indent, args.assertions))


def run(args=None, config=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Synchronize ledger.")
    parser.add_argument(
        "fpath", type=str, metavar="FILE", help="csv file to be ingested."
    )
    parser.add_argument(
        "-a",
        "--account",
        type=str,
        default=None,
        help="account name for the file provided",
    )
    parser.add_argument(
        "-l",
        "--ledger",
        type=str,
        default=None,
        help="specify ledger file to READ for syncing",
        metavar="LEDGER_FILE",
    )
    parser.add_argument(
        "--rules",
        type=str,
        default=None,
        help="specify rule file to READ for Payee matching",
    )
    parser.add_argument(
        "-i",
        "--indent",
        type=int,
        default=4,
        help="number of spaces to use for indentation",
    )
    parser.add_argument(
        "--unknown-account",
        type=str,
        dest="unknownaccount",
        default=None,
        help="specify account name to use when one can't be \
found by payee",
    )
    parser.add_argument(
        "--no-assertions",
        action="store_false",
        dest="assertions",
        help="do not append balance assertions",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="enable debug logging",
    )
    parser.add_argument(
        "--payee-format",
        type=str,
        default=None,
        dest="payee_format",
        help="""Format string to use for generating the payee line. Substitutions
        can be written using {memo}, {payee}, {txntype}, {account} or
        {tferaction} for OFX. If the input file is a CSV file,
        substitutions are written using the CSV file column names
        between {}.""",
    )
    parser.add_argument(
        "-y",
        "--date-format",
        type=str,
        default=None,
        dest="date_format",
        help="""Format string to use for printing dates.
                        See strftime for details on format string syntax. Default is "%%Y/%%m/%%d".""",
    )
    args = parser.parse_args(args)

    ledger_file = None
    if args.ledger:
        ledger_file = args.ledger
    else:
        ledger_file = find_ledger_file()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    ledger = Ledger(ledger_file=ledger_file, no_pipe=True)

    if args.rules and Path(args.rules).exists():
        with open(args.rules) as f:
            for line in f:
                regex, account = line.strip().split("\t")
                ledger.add_rule(re.compile(regex, re.IGNORECASE), account)

    import_csv(ledger, args)
