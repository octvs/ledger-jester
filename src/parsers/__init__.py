# isort: skip_file
from parsers.parser import Parser
from parsers.registry import PARSER_REGISTRY, get_parser, register_parser

# trigger discovery of all bank parsers via banks/__init__.py
from parsers import banks  # noqa: F401

__all__ = ["Parser", "PARSER_REGISTRY", "get_parser", "register_parser"]
