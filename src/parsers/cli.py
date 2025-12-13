#!/usr/bin/env python

import argparse
import logging
import sys

from parsers import parser_factory


def run():
    args = sys.argv[1:]
    if args is None:
        print("Must provide a parser to use.")

    parser = argparse.ArgumentParser(
        description="Parse bank exports for ledger-jedger."
    )
    parser.add_argument(
        "parser", type=str, metavar="PARSER", help="parser type to be invoked."
    )
    parser.add_argument(
        "fpath", type=str, metavar="FILE", help="csv file to be ingested."
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="enable debug logging",
    )
    args = parser.parse_args(args)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    parser = parser_factory(args.parser)
    parser.parse(args.fpath)
