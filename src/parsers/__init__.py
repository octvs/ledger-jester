"""Bank export parsers: convert raw exports into monthly CSV chunks.

See parsers.parser.Parser for the base contract every bank-specific
parser implements, and parsers.banks for concrete implementations.
"""

from parsers.parser import Parser
from registry import Registry


class ParserRegistry(Registry):
    """Registry for parser implementations."""

    TYPE = "parser"


REGISTRY = ParserRegistry()

# Run last to initialize all bank implementations after rest is done
from parsers import banks  # noqa: F401, E402

__all__ = ["Parser", "REGISTRY"]
