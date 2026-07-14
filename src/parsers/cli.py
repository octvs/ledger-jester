import argparse


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    parse_cmd = subparsers.add_parser(
        "parse", help="Parse bank exports to use with ledger-jester."
    )
    parse_cmd.add_argument(
        "fpath", type=str, metavar="FILE", help="Export file to be parsed."
    )
    parse_cmd.set_defaults(func=run)


def run(args: argparse.Namespace) -> None:
    print("Parsing exports...")
