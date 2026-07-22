"""Generic name -> class registry for building extensible plugin systems.

This module provides a Registry class. Each submodule (e.g. "parsers", "sync")
can extend this to create its own registry.

Typical usage:

foo/__init__.py

    from registry import Registry

    class ModuleRegistry(Registry):
        TYPE = "my-module"

    REGISTRY = ModuleRegistry()

foo/sub_module/bar.py

    from foo import REGISTRY

    @REGISTRY.register
    class Bar:
        TYPE = "bar"
        ...

baz.py

    from foo import REGISTRY

    bar_class = REGISTRY.get("bar")  # -> Bar()
"""

from typing import Generic, Type, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    """Base Registry class, maps string TYPE keys directly to classes."""

    def __init__(self) -> None:
        """Initialize registry with empty dictionary."""
        self._bucket: dict[str, Type[T]] = {}

    def register(self, cls: Type[T]) -> Type[T]:
        """Register a class using its `TYPE` attribute."""
        type_ = getattr(cls, "TYPE", None)
        if not type_:
            raise ValueError(
                f"Class '{cls.__name__}' must define a 'TYPE' attribute."
            )
        if type_ in self._bucket:
            raise ValueError(f"TYPE {type_!r} is already registered.")
        self._bucket[type_] = cls
        return cls

    def get(self, key: str) -> Type[T]:
        """Retrieve class by string key."""
        if key not in self._bucket:
            raise KeyError(
                f"No plugin registered for TYPE {key!r}. "
                f"Available: {list(self._bucket.keys())}"
            )
        return self._bucket[key]
