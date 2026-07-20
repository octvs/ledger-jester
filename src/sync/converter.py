"""TODO."""

from registry import REGISTRY, get

DOMAIN = "converters"


def converter_factory(fieldset: list) -> object:
    """Provide the fitting converter based on columns of the csv file. TODO."""
    for _type, klass in REGISTRY[DOMAIN].items():
        if set(klass("none").COLS.values()) <= set(fieldset):
            return get(DOMAIN, _type)
    raise NotImplementedError
