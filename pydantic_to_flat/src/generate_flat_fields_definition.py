from types import NoneType, UnionType
from typing import Any, _UnionGenericAlias

import pydantic
from pydantic.fields import FieldInfo

DEFAULT_FLAT_TYPES = (bool, int, float, str, bytes, NoneType)
PydanticFieldDefinition = tuple[type, FieldInfo]
JSON_STR = "JSON"  # this value is checked in field description to decide whether to load/dump from json.


def generate_flat_fields_definition_dict(
        cls: type[pydantic.BaseModel], flat_types: tuple = DEFAULT_FLAT_TYPES
) -> dict[str, PydanticFieldDefinition]:
    """
    Generates a dict of flattened pydantic fields definition (info & annotation).
    Any field that is not supported by 'FlatField' definition, will be flattened into str.
    """
    return {
        field_name:
            (field_info.annotation, field_info)
            if is_type_included(field_info.annotation, flat_types)
            else (str, FieldInfo(annotation=str, required=True, description=JSON_STR))
        for field_name, field_info in cls.model_fields.items()
    }


def is_type_included(inspected_type: type, types_tuple: tuple[type]) -> bool:
    """
    Returns True if 'sub_type' is a subtype of 'super_type'.
    Supports Optional fields.
    """
    def is_union(t: Any) -> bool:
        return isinstance(t, (_UnionGenericAlias, UnionType))

    def reduce_optional_to_simple_type(union_type: _UnionGenericAlias | UnionType) -> Any:
        types = [t for t in union_type.__args__ if t != NoneType]
        assert len(types) == 1, "Union of multiple types is not supported, except for None / Optional"
        return types[0]

    if is_union(inspected_type):
        inspected_type = reduce_optional_to_simple_type(inspected_type)
    return issubclass(inspected_type, types_tuple)


def validate_flat_pydantic_model(model: type[pydantic.BaseModel], flat_fields: tuple = DEFAULT_FLAT_TYPES) -> None:
    assert issubclass(model, pydantic.BaseModel)
    for field_info in model.model_fields.values():
        assert is_type_included(field_info.annotation, flat_fields)
