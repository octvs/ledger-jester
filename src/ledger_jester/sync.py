import argparse


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    sync_cmd = subparsers.add_parser("sync", help="Sync ledger data")
    sync_cmd.add_argument(
        "fpath", type=str, metavar="FILE", help="Csv file to be synced."
    )
    sync_cmd.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    print("Syncing ledger data...")
