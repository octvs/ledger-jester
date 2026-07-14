import argparse

from parsers import PARSER_REGISTRY, get_parser


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parse_cmd = subparsers.add_parser(
        "parse", help="Parse bank exports to use with ledger-jester."
    )
    parse_cmd.add_argument(
        "type",
        choices=list(PARSER_REGISTRY.keys()),
        help="Parser type to use",
    )
    parse_cmd.add_argument(
        "fpath", type=str, metavar="FILE", help="Export file to be parsed."
    )
    parse_cmd.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    """Run the 'parse' subcommand.

    Args:
        args: Parsed CLI arguments containing 'fpath' and 'type'.
    """
    parser = get_parser(args.type)
    parser.parse(args.fpath)
