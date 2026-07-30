"""'sync' subcommand: sync a bank export to your ledger database."""

import argparse
import logging
from pathlib import Path

from convert import REGISTRY as converter_registry
from parse import REGISTRY as parser_registry


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'sync' subcommand.

    Args:
        subparsers: The subparsers action from the parent ArgumentParser.

    """
    sync_cmd = subparsers.add_parser("sync", help="Sync ledger data.")
    sync_cmd.add_argument(
        "type",
        choices=list(parser_registry._bucket.keys()),
        help="Parser type to use.",
    )
    sync_cmd.add_argument(
        "account",
        type=str,
        metavar="ACCT",
        help="Target account.",
    )
    sync_cmd.add_argument(
        "fpaths",
        type=Path,
        metavar="FILE",
        help="File to be synced.",
        nargs="+",
    )
    sync_cmd.set_defaults(func=main)


def main(args: argparse.Namespace) -> None:
    """Run the 'parse' subcommand.

    Args:
        args: Parsed CLI arguments containing 'type', 'account' and 'fpaths'.

    """
    converter = converter_registry.get(args.type)(args.account)
    parser = parser_registry.get(args.type)()
    for fpath in args.fpaths:
        parser.assert_path(fpath)
        df = parser.read_file(fpath).sort_values(by="dt")
        logging.info(f"Read {fpath} from disk.")
        df = df.astype(str)  # Cast to str to get consistent hashes w/ convert
        for _row in df.to_dict(orient="records"):
            row = converter.ROW_TYPE.from_dict(_row)
            if not (converter.skip_row(row) or converter.is_row_synced(row)):
                xact = converter.convert(row)
                if xact:
                    print(xact)
