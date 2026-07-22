"""'parse' subcommand: convert a bank export into monthly CSV chunks."""

import argparse

from parsers import REGISTRY


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
        "fpath", type=str, metavar="FILE", help="Export file to be parsed."
    )
    parse_cmd.set_defaults(func=main)


def main(args: argparse.Namespace) -> None:
    """Run the 'parse' subcommand.

    Args:
        args: Parsed CLI arguments containing 'fpath' and 'type'.

    """
    parser = REGISTRY.get(args.type)()
    parser.parse(args.fpath)
