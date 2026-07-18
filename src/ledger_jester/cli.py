"""'sync' subcommand: sync a CSV export into the ledger file."""

import argparse


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'sync' subcommand.

    Args:
        subparsers: The subparsers action from the parent ArgumentParser.

    """
    sync_cmd = subparsers.add_parser("sync", help="Sync ledger data")
    sync_cmd.add_argument(
        "fpath", type=str, metavar="FILE", help="Csv file to be synced."
    )
    sync_cmd.set_defaults(func=main)


def main(args: argparse.Namespace) -> None:
    """Run the 'sync' subcommand.

    Args:
        args: Parsed CLI arguments containing 'fpath'.

    """
    print("Syncing ledger data...")
