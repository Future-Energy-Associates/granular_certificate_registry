from typing import (
    AbstractSet,
    Any,
    Mapping,
    Sequence,
    Union,
)

from sqlalchemy import Column
from sqlmodel import Field

field_attrs = [
    "default",
    "default_factory",
    "alias",
    "title",
    "description",
    "include",
    "const",
    "gt",
    "ge",
    "lt",
    "le",
    "multiple_of",
    "min_items",
    "max_items",
    "min_length",
    "max_length",
    "allow_mutation",
    "regex",
    "primary_key",
    "foreign_key",
    "nullable",
    "index",
    "sa_column",
    "sa_column_args",
    "sa_column_kwargs",
    "schema_extra",
]


def item_field(
    item,
    default: Any = None,
    *args,
    default_factory: Any | None = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclude: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    include: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    const: bool | None = None,
    gt: float | None = None,
    ge: float | None = None,
    lt: float | None = None,
    le: float | None = None,
    multiple_of: float | None = None,
    min_items: int | None = None,
    max_items: int | None = None,
    min_length: int | None = None,
    max_length: int | None = None,
    allow_mutation: bool = True,
    regex: str | None = None,
    primary_key: bool = False,
    foreign_key: Any | None = None,
    nullable: Union[bool, Any] = None,
    index: Union[bool, Any] = None,
    sa_column: Union[Column, Any] = None,  # type: ignore
    sa_column_args: Union[Sequence[Any], Any] = None,
    sa_column_kwargs: Union[Mapping[str, Any], Any] = None,
    schema_extra: dict[str, Any] | None = None,
    **kwargs,
):
    # Everything apart from the item is optional
    # First do a hasattr pass and add if so
    # Then work through anything passed as a param
    locals_ = locals()
    kwargs = {}

    for attr in field_attrs:
        if hasattr(item, attr):
            kwargs.update({attr: getattr(item, attr)})

        if hasattr(locals_, attr):
            kwargs.update({attr: getattr(locals_, attr)})

    field = Field(*args, **kwargs)

    return field
