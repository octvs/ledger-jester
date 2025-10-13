#!/usr/bin/env python

import argparse
import logging
import os
import os.path
import re
import sys

from ledger_jester import LedgerAutosyncException
from ledger_jester.ledgerwrap import Ledger
from ledger_jester.sync import CsvSynchronizer


def find_ledger_file(ledgerrcpath=None):
    """Returns main ledger file path or raise exception if it cannot be \
found."""
    if ledgerrcpath is None:
        ledgerrcpath = os.path.abspath(os.path.expanduser("~/.ledgerrc"))
    if "LEDGER_FILE" in os.environ:
        return os.path.abspath(os.path.expanduser(os.environ["LEDGER_FILE"]))
    elif os.path.exists(ledgerrcpath):
        # hacky
        ledgerrc = open(ledgerrcpath)
        for line in ledgerrc.readlines():
            md = re.match(r"--file\s+([^\s]+).*", line)
            if md is not None:
                return os.path.abspath(os.path.expanduser(md.group(1)))
    else:
        return None


def print_results(converter, ofx, ledger, txns, args):
    """
    This function is the final common pathway of program:

    Print initial balance if requested;
    Print transactions surviving de-duplication filter;
    Print balance assertions if requested;
    Print commodity prices obtained from position statements
    """

    for txn in txns:
        print(converter.convert(txn).format(args.indent))
    if args.assertions:
        print(converter.format_balance(ofx.account.statement))

    # if OFX has positions use these to obtain commodity prices
    # and print "P" records to provide dated/timed valuations
    # Note that this outputs only the commodity price,
    # not your position (e.g. # shares), even though this is in the OFX record
    if hasattr(ofx.account.statement, "positions"):
        for pos in ofx.account.statement.positions:
            print(converter.format_position(pos))


def import_csv(ledger, args):
    if args.account is None:
        raise Exception(
            "When importing a CSV file, you must specify an account name."
        )
    sync = CsvSynchronizer(
        ledger, payee_format=args.payee_format, date_format=args.date_format
    )
    txns = sync.parse_file(
        args.PATH, accountname=args.account, unknownaccount=args.unknownaccount
    )
    if args.reverse:
        txns = reversed(txns)
    for txn in txns:
        if txn is not None:
            print(txn.format(args.indent, args.assertions))


def run(args=None, config=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Synchronize ledger.")
    parser.add_argument(
        "PATH",
        nargs="?",
        help="do not sync; import from OFX \
file",
    )
    parser.add_argument(
        "-a",
        "--account",
        type=str,
        default=None,
        help="sync only the named account; \
if importing from file, set account name for import",
    )
    parser.add_argument(
        "-l",
        "--ledger",
        type=str,
        default=None,
        help="specify ledger file to READ for syncing",
    )
    parser.add_argument(
        "--rules",
        type=str,
        default=None,
        help="specify rule file to READ for Payee matching",
    )
    parser.add_argument(
        "-L",
        "--no-ledger",
        dest="no_ledger",
        action="store_true",
        default=False,
        help="do not de-duplicate against a ledger file",
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
        "--assertions",
        action="store_true",
        default=False,
        help="create balance assertion entries",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
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
        "--reverse",
        action="store_true",
        default=False,
        help="print CSV transactions in reverse order",
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
    if args.ledger and args.no_ledger:
        raise LedgerAutosyncException(
            "You cannot specify a ledger file and -L"
        )
    elif args.ledger:
        ledger_file = args.ledger
    else:
        ledger_file = find_ledger_file()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if ledger_file is None:
        sys.stderr.write(
            "LEDGER_FILE environment variable not set, and no \
.ledgerrc file found, and -l argument was not supplied: running with deduplication disabled. \
All transactions will be printed!\n"
        )
        ledger = None
    elif args.no_ledger:
        ledger = None
    else:
        ledger = Ledger(ledger_file=ledger_file, no_pipe=True)

    if args.rules and os.path.exists(args.rules):
        with open(args.rules) as f:
            for line in f:
                regex, account = line.strip().split("\t")
                ledger.add_rule(re.compile(regex, re.IGNORECASE), account)

    _, file_extension = os.path.splitext(args.PATH.lower())
    import_csv(ledger, args)


if __name__ == "__main__":
    run()
