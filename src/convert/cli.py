"""'convert' subcommand: convert a CSV export into the ledger file."""

import argparse
import csv
from pathlib import Path

from convert import REGISTRY


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'convert' subcommand.

    Args:
        subparsers: The subparsers action from the parent ArgumentParser.

    """
    convert_cmd = subparsers.add_parser("convert", help="Convert to ledger.")
    convert_cmd.add_argument(
        "account",
        type=str,
        metavar="ACCT",
        help="Target account.",
    )
    convert_cmd.add_argument(
        "fpath", type=Path, metavar="FILE", help="Csv file to be converted."
    )
    convert_cmd.set_defaults(func=main)


def main(args: argparse.Namespace) -> None:
    """Run the 'convert' subcommand.

    Args:
        args: Parsed CLI arguments containing 'fpath'.

    """
    with open(args.fpath, mode="r", newline="") as f:
        content = csv.DictReader(f)
        if not content.fieldnames:
            raise ValueError(f"Given file is empty: {args.fpath}")
        converter = REGISTRY.get(content.fieldnames)(args.account)
        for row in content:
            row = converter.ROW_TYPE.from_dict(row)
            if not (converter.skip_row(row) or converter.is_row_synced(row)):
                xact = converter.convert(row)
                if xact:
                    print(xact)
