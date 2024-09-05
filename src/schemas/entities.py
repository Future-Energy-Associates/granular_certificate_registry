from typing import (
    AbstractSet,
    Any,
    Mapping,
    Optional,
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
    default_factory: Optional[Any] = None,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    exclude: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    include: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allow_mutation: bool = True,
    regex: Optional[str] = None,
    primary_key: bool = False,
    foreign_key: Optional[Any] = None,
    nullable: Union[bool, Any] = None,
    index: Union[bool, Any] = None,
    sa_column: Union[Column, Any] = None,  # type: ignore
    sa_column_args: Union[Sequence[Any], Any] = None,
    sa_column_kwargs: Union[Mapping[str, Any], Any] = None,
    schema_extra: Optional[dict[str, Any]] = None,
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
