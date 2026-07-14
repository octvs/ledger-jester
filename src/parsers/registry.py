from parsers.parser import Parser

PARSER_REGISTRY: dict[str, type[Parser]] = {}


def register_parser(cls: type[Parser]) -> type[Parser]:
    """Class decorator that registers a Parser subclass by its TYPE.

    Args:
        cls (type[Parser]): The Parser subclass to register.

    Returns:
        type[Parser]: The same class, unmodified.

    Raises:
        ValueError: If TYPE is not set, or if TYPE is already registered.
    """
    if cls.TYPE is None:
        raise ValueError(f"{cls.__name__} must set a TYPE before registering")

    if cls.TYPE in PARSER_REGISTRY:
        raise ValueError(
            f"Parser TYPE {cls.TYPE!r} is already registered "
            f"to {PARSER_REGISTRY[cls.TYPE].__name__}"
        )

    PARSER_REGISTRY[cls.TYPE] = cls
    return cls


def get_parser(type_: str) -> Parser:
    """Instantiate a registered parser by its TYPE string.

    Args:
        type_ (str): The registered TYPE identifier.

    Returns:
        Parser: A new instance of the matching Parser subclass.

    Raises:
        KeyError: If no parser is registered under the given type.
    """
    if type_ not in PARSER_REGISTRY:
        raise KeyError(
            f"No parser registered for type {type_!r}. "
            f"Available types: {list(PARSER_REGISTRY.keys())}"
        )
    return PARSER_REGISTRY[type_]()
