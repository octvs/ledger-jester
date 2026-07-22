"""TODO."""

from typing import Sequence, Type

from registry import Registry, T


class ConverterRegistry(Registry):
    """Registry for converters, with overriden get method for auto-discovery."""

    TYPE = "converter"

    def get(self, key: str | Sequence[str]) -> Type[T]:
        """Fetch matching converter with auto-discovery.

        If `key` is a list of strings fetch the supporting converter from
        registered converters. If `key` is a string, fall back to standard base
        lookup.
        """
        if isinstance(key, str) and key in self._bucket:
            return super().get(key)

        for _type, klass in self._bucket.items():
            if set(klass.COLS.values()) == set(key):
                return klass

        raise NotImplementedError(
            f"No suitable converter found for columns: {key}"
        )


REGISTRY = ConverterRegistry()

# Must run last to initialize after the rest
from sync import banks  # noqa: F401, E402
