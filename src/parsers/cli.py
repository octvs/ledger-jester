import argparse

from parsers.parser import DOMAIN
from registry import REGISTRY, get


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parse_cmd = subparsers.add_parser(
        "parse", help="Parse bank exports to use with ledger-jester."
    )
    parse_cmd.add_argument(
        "type",
        choices=list(REGISTRY.get(DOMAIN, {}).keys()),
        help="Parser type to use",
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
    parser = get(DOMAIN, args.type)
    parser.parse(args.fpath)
