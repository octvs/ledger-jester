"""Top-level CLI entry point for ledger-jester.

Builds the argument parser, wires up each subcommand module, and
dispatches to the selected subcommand's handler.
"""

import argparse
import logging

from ledger_jester.cli import add_subparser as add_sync_subcmd
from parsers.cli import add_subparser as add_parse_subcmd


def build_argparser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands wired up.

    Returns:
        The fully configured ArgumentParser, ready to parse sys.argv.

    """
    argparser = argparse.ArgumentParser(prog="ledger-j")
    subparsers = argparser.add_subparsers(dest="command", required=True)

    add_parse_subcmd(subparsers)
    add_sync_subcmd(subparsers)

    argparser.add_argument(
        "--verbose",
        "-v",
        dest="log_level",
        action="append_const",
        const=10,
    )

    return argparser


def run() -> None:
    """Parse CLI arguments and dispatch to the selected subcommand."""
    argparser = build_argparser()
    args = argparser.parse_args()
    if args.log_level:
        log_level = max(logging.DEBUG, logging.WARNING - sum(args.log_level))
        logging.getLogger().setLevel(log_level)
    logging.debug(f"Received args: {args}")
    args.func(args)


if __name__ == "__main__":
    run()
