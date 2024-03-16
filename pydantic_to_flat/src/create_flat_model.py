from datetime import datetime
from types import NoneType, UnionType
from typing import Any, _UnionGenericAlias

import pydantic
from pydantic.fields import FieldInfo


PydanticFieldDefinition = tuple[type, FieldInfo]
# Used to create pydantic BaseModel dynamically


_DEFAULT_FLAT_TYPES = (bool, int, float, str, bytes, NoneType, datetime)
# Used to check whether a field has a flat type or a composite one.
# Composite includes lists, dicts, pydantic classes


# The following keys are stored in pydantic model's FieldInfo.json_schema_extra
# to mark a field as json or datetime with fixed timezone:
JSON_KEY_MARK = "json"
FIXED_TIMEZONE_KEY_MARK = "fixed_timezone"


_JSON_FIELD_DEFINITION: PydanticFieldDefinition = (
    str,
    FieldInfo(annotation=str, required=True, json_schema_extra={JSON_KEY_MARK: True})
    # Composite fields are converted into JSON (flat string fields).
    # They are marked by the "json" key in json_schema_extra
)


def create_flat_model(cls: type[pydantic.BaseModel], fixed_timezone: str = "") -> type[pydantic.BaseModel]:
    """
    Returns a flat pydantic model, dynamically generated from a given pydantic.BaseModel class
    """
    flat_model = pydantic.create_model(
        f"{cls.__name__}FlatModel",
        **generate_flat_fields_definition_dict(cls, fixed_timezone),
    )
    validate_flat_pydantic_model(flat_model)
    return flat_model


def generate_flat_fields_definition_dict(
        cls: type[pydantic.BaseModel],
        fixed_timezone: str = "",
        flat_types: tuple = _DEFAULT_FLAT_TYPES
) -> dict[str, PydanticFieldDefinition]:
    """
    Generates a dict of flattened pydantic fields definition (annotation & info).
    Flat fields (recognized by their type, which must be one of 'flat_types'), keep their annotation & info.
    Composite fields (with type other than 'flat_types'), are flattened into a '_JSON_FIELD_DEFINITION'.
    """
    def set_fixed_timezone_in_field_info(field_info: FieldInfo) -> None:
        if field_info.json_schema_extra is None:
            field_info.json_schema_extra = {FIXED_TIMEZONE_KEY_MARK: fixed_timezone}
        else:
            field_info.json_schema_extra[FIXED_TIMEZONE_KEY_MARK] = fixed_timezone

    def is_flat_field_type(field_info: FieldInfo) -> bool:
        return is_type_included(field_info.annotation, flat_types)

    def is_datetime_type(field_info: FieldInfo) -> bool:
        return is_type_included(field_info.annotation, (datetime,))

    flat_definition = dict({})
    for field_name, field_info in cls.model_fields.items():
        if is_flat_field_type(field_info):
            flat_definition[field_name] = (field_info.annotation, field_info)
            if fixed_timezone and is_datetime_type(field_info):
                set_fixed_timezone_in_field_info(field_info)
        else:
            flat_definition[field_name] = _JSON_FIELD_DEFINITION
    return flat_definition


def is_type_included(inspected_type: type, types_tuple: tuple[type]) -> bool:
    """
    Returns True if 'sub_type' is a subtype of 'super_type'.
    Supports Optional fields.
    """
    def is_union(t: Any) -> bool:
        return isinstance(t, (_UnionGenericAlias, UnionType))

    def reduce_optional_to_simple_type(union_type: _UnionGenericAlias | UnionType) -> Any:
        types = [t for t in union_type.__args__ if t != NoneType]
        assert len(types) == 1, f"{union_type=} - Union of multiple types is not supported, except for None / Optional"
        return types[0]

    if is_union(inspected_type):
        inspected_type = reduce_optional_to_simple_type(inspected_type)
    return issubclass(inspected_type, types_tuple)


def validate_flat_pydantic_model(model: type[pydantic.BaseModel], flat_fields: tuple = _DEFAULT_FLAT_TYPES) -> None:
    assert issubclass(model, pydantic.BaseModel), f"{type(model)=} - Flat pydantic model must be of type pydantic.BaseModel"
    for field_info in model.model_fields.values():
        assert is_type_included(field_info.annotation, flat_fields), f"{field_info.annotation=} - Flat pydantic model must have only flat fields"
