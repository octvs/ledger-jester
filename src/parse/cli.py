"""'parse' subcommand: convert a bank export into monthly CSV chunks."""

import argparse
from pathlib import Path

from parse import REGISTRY


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'parse' subcommand.

    Args:
        subparsers: The subparsers action from the parent ArgumentParser.

    """
    parse_cmd = subparsers.add_parser(
        "parse", help="Parse bank exports to use with ledger-jester."
    )
    parse_cmd.add_argument(
        "type",
        choices=list(REGISTRY._bucket.keys()),
        help="Parser type to use.",
    )
    parse_cmd.add_argument(
        "fpaths",
        type=Path,
        metavar="FILES",
        help="Files to be parsed.",
        nargs="+",
    )
    parse_cmd.set_defaults(func=main)


def main(args: argparse.Namespace) -> None:
    """Run the 'parse' subcommand.

    Args:
        args: Parsed CLI arguments containing 'type' and 'fpath'.

    """
    parser = REGISTRY.get(args.type)()
    for fpath in args.fpaths:
        parser.parse(fpath)
