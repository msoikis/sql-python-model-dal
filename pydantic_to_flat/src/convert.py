from datetime import datetime
from typing import Type, Any, Optional
from zoneinfo import ZoneInfo

import pydantic

from .create_flat_model import validate_flat_pydantic_model, JSON_KEY_MARK, FIXED_TIMEZONE_KEY_MARK


def to_flat_model[T: pydantic.BaseModel](py_obj: pydantic.BaseModel, flat_model: Type[T]) -> T:
    """
    Converts py_obj to a flat_model and returns the new instance.
    For each target flat field (recognized by field json_schema_extra "json" key),
    the source field is converted into json represented string.
    If fixed_timezone is set, all datetime fields must have the same timezone as the fixed_timezone.
    """
    def convert_to_json(value: Any) -> str:
        return _build_field_model(py_obj.__class__, key)(value).model_dump_json()

    def verify_fixed_timezone_for_datetime_field(key: str, value: Any) -> None:
        if fixed_timezone := get_field_fixed_timezone(flat_model.model_fields[key]):
            if isinstance(value, datetime):
                assert value.tzinfo == ZoneInfo(
                    fixed_timezone), f"datetime field ({key}={value}) must have the same timezone as the fixed_timezone ({fixed_timezone})"

    assert isinstance(py_obj, pydantic.BaseModel), f"py_obj={repr(py_obj)} must be a pydantic.BaseModel class/subclass"
    validate_flat_pydantic_model(flat_model)
    flat_dict = dict({})
    for key, value in py_obj.model_dump().items():
        if is_json_str_field(flat_model.model_fields[key]):
            flat_dict[key] = convert_to_json(value)
        else:
            flat_dict[key] = value
            verify_fixed_timezone_for_datetime_field(key, value)
    return flat_model(**flat_dict)


def from_flat_model[T: pydantic.BaseModel](flat_obj: pydantic.BaseModel, py_model: Type[T]) -> T:
    """
    Converts flat_obj to a py_model and returns the new instance.
    For each source field that was flattened (recognized by field's json_schema_extra "json" key),
    the target field is loaded and built from the source json string field.
    If fixed_timezone is set, all naive (without timezone) target datetime fields are set to fixed_timezone.
    """
    def load_from_json(field_name: str, value: Any) -> Any:
        return _build_field_model(py_model, field_name).model_validate_json(value).root

    def apply_fixed_timezone_to_datetime_if_relevant(field_name: str, dt_field: datetime) -> None:
        flat_field_info = flat_obj.model_fields[field_name]
        fixed_timezone = get_field_fixed_timezone(flat_field_info)
        if fixed_timezone and isinstance(dt_field, datetime):
            if dt_field.tzinfo is None:
                dt_field = dt_field.replace(tzinfo=ZoneInfo(fixed_timezone))
            assert dt_field.tzinfo == ZoneInfo(fixed_timezone), f"datetime field ({field_name}={dt_field}) must have the same timezone as the fixed_timezone ({fixed_timezone})"

    class Undefined:
        pass

    assert isinstance(flat_obj, pydantic.BaseModel), f"flat_obj={repr(flat_obj)} must be a pydantic.BaseModel class/subclass"
    py_dict: dict[str, Any] = {}
    for field_name, py_field_info in py_model.model_fields.items():
        flat_field = getattr(flat_obj, field_name, Undefined)
        if flat_field == Undefined:
            continue
        if is_json_str_field(flat_obj.model_fields[field_name]):
            py_dict[field_name] = load_from_json(field_name, flat_field)
        else:
            py_dict[field_name] = flat_field
            apply_fixed_timezone_to_datetime_if_relevant(field_name, flat_field)
    return py_model(**py_dict)


def _build_field_model(py_model: type[pydantic.BaseModel], field_name: str) -> type[pydantic.RootModel]:
    # Uses pydantic.RootModel to convert to/from json
    return pydantic.RootModel[py_model.model_fields[field_name].annotation]


def is_json_str_field(field_info: pydantic.fields.FieldInfo) -> bool:
    return field_info.json_schema_extra and field_info.json_schema_extra.get(JSON_KEY_MARK, None)


def get_field_fixed_timezone(field_info: pydantic.fields.FieldInfo) -> Optional[str]:
    if field_info.json_schema_extra is None:
        return None
    return field_info.json_schema_extra.get(FIXED_TIMEZONE_KEY_MARK, None)
