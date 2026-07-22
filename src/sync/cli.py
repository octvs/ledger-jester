"""'sync' subcommand: sync a CSV export into the ledger file."""

import argparse
import csv

from sync import REGISTRY


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'sync' subcommand.

    Args:
        subparsers: The subparsers action from the parent ArgumentParser.

    """
    sync_cmd = subparsers.add_parser("sync", help="Sync ledger data.")
    sync_cmd.add_argument(
        "fpath", type=str, metavar="FILE", help="Csv file to be synced."
    )
    sync_cmd.add_argument(
        "account",
        type=str,
        metavar="ACCT",
        help="Target account.",
    )
    sync_cmd.set_defaults(func=main)


def main(args: argparse.Namespace) -> None:
    """Run the 'sync' subcommand.

    Args:
        args: Parsed CLI arguments containing 'fpath'.

    """
    with open(args.fpath, mode="r", newline="") as f:
        content = csv.DictReader(f)
        if not content.fieldnames:
            raise ValueError(f"Given file is empty: {args.fpath}")
        converter = REGISTRY.get(content.fieldnames)(args.account)
        for row in content:
            if not converter.is_row_synced(row):
                xact = converter.convert(row)
                if xact:
                    print(xact)
