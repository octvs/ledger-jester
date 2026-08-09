"""Top-level CLI entry point for ledger-jester.

Builds the argument parser, wires up each subcommand module, and
dispatches to the selected subcommand's handler.
"""

import argparse
import logging

from convert.cli import add_subparser as add_convert_subcmd
from parse.cli import add_subparser as add_parse_subcmd
from sync.cli import add_subparser as add_sync_subcmd


def build_argparser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands wired up.

    Returns:
        The fully configured ArgumentParser, ready to parse sys.argv.

    """
    argparser = argparse.ArgumentParser(prog="ledger-j")
    subparsers = argparser.add_subparsers(dest="command", required=True)
    add_convert_subcmd(subparsers)
    add_parse_subcmd(subparsers)
    add_sync_subcmd(subparsers)
    argparser.add_argument("--verbose", "-v", action="count", default=0)
    return argparser


def run() -> None:
    """Parse CLI arguments and dispatch to the selected subcommand."""
    argparser = build_argparser()
    args = argparser.parse_args()
    log_level = max(logging.DEBUG, logging.WARNING - args.verbose * 10)
    logging.getLogger().setLevel(log_level)
    logging.debug(f"Received args: {args}")
    args.func(args)


if __name__ == "__main__":
    run()
