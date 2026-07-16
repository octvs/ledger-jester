"""Bank export parsers: convert raw exports into monthly CSV chunks.

See parsers.parser.Parser for the base contract every bank-specific
parser implements, and parsers.banks for concrete implementations.
"""

from parsers import banks  # noqa: F401
from parsers.parser import DOMAIN, Parser

__all__ = ["DOMAIN", "Parser"]
