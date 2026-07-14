"""Auto-discovery for bank-specific parser implementations.

Every module placed in this package is automatically imported so that
its @register_parser decorator executes and the parser becomes
available via PARSER_REGISTRY. Adding a new bank requires no manual
wiring beyond creating the file here.
"""

import importlib
import pkgutil

for _, module_name, _ in pkgutil.iter_modules(__path__):
    importlib.import_module(f"{__name__}.{module_name}")
