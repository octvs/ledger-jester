"""'sync' subcommand: sync a CSV export into the ledger file."""

import argparse
import csv

from converters.revolut import RevolutConverter


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
    sync = RevolutConverter(args.account)
    with open(args.fpath, mode="r", newline="") as f:
        content = csv.DictReader(f)
        for row in content:
            if not sync.is_row_synced(row):
                xact = sync.convert(row)
                if xact:
                    print(xact)
