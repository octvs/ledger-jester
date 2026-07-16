"""Generic name -> class registry for building extensible plugin systems.

This module provides a single global REGISTRY, organized as a dict of
independent namespaces ("domains"). Each domain (e.g. "parsers", "sync")
maps TYPE strings to classes, allowing unrelated plugin systems to share
the same registration mechanism without risking name collisions between
domains.

Typical usage, within a specific domain's own module:

    from registry import register, get

    DOMAIN = "parsers"

    @register(DOMAIN)
    class RevolutParser(Parser):
        TYPE = "revolut"
        ...

    parser = get(DOMAIN, "revolut")  # -> RevolutParser()
"""

from typing import TypeVar

T = TypeVar("T")

REGISTRY: dict[str, dict[str, type]] = {}
"""The global registry: REGISTRY[domain][type_] -> class."""


def register(domain: str):
    """Return a decorator that registers a class under a given domain.

    The returned decorator reads the class's TYPE attribute and stores
    the class in REGISTRY[domain][TYPE]. The class itself is returned
    unmodified, so decorating a class with this has no effect on its
    runtime behavior beyond the registration side effect.

    Args:
        domain: Namespace to register under (e.g. "parsers", "sync").
            Each domain is independent, so the same TYPE string may be
            reused across different domains without conflict.

    Returns:
        A decorator function that, when applied to a class, registers
        it and returns it unchanged.

    Raises:
        ValueError: If the decorated class has no TYPE attribute set,
            or if that TYPE is already registered within this domain.

    """
    bucket = REGISTRY.setdefault(domain, {})

    def decorator(cls: type[T]) -> type[T]:
        type_ = getattr(cls, "TYPE", None)
        if type_ is None:
            raise ValueError(
                f"{cls.__name__} must set a TYPE before registering under {domain!r}"
            )
        if type_ in bucket:
            raise ValueError(
                f"{domain!r} TYPE {type_!r} is already registered "
                f"to {bucket[type_].__name__}"
            )
        bucket[type_] = cls
        return cls

    return decorator


def get(domain: str, type_: str) -> T:
    """Instantiate a registered class by domain and TYPE string.

    Args:
        domain: The namespace to look up (e.g. "parsers", "sync").
        type_: The registered TYPE identifier within that domain.

    Returns:
        A new instance of the matching class.

    Raises:
        KeyError: If domain or type_ isn't registered. Note that an
            unknown domain and an unknown type_ within a known domain
            both raise the same error; the message's "Available" list
            will be empty in the former case.

    """
    bucket = REGISTRY.get(domain, {})
    if type_ not in bucket:
        raise KeyError(
            f"No {domain!r} registered for type {type_!r}. "
            f"Available: {list(bucket.keys())}"
        )
    return bucket[type_]()
