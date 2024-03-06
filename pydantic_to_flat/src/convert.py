from typing import Type, Any

import pydantic

from .generate_flat_fields_definition import validate_flat_pydantic_model, JSON_STR


def to_flat_model[T: pydantic.BaseModel](py_obj: pydantic.BaseModel, flat_model: Type[T]) -> T:
    """
    Converts py_obj to a flat_model and returns the new instance.
    For each target flat field with field description of JSON_STR, the source field is converted into json represented string.
    """
    assert isinstance(py_obj, pydantic.BaseModel)
    validate_flat_pydantic_model(flat_model)
    flat_dict: dict[str, Any] = {
        key: _build_field_model(py_obj.__class__, key)(value).model_dump_json()
        if flat_model.model_fields[key].description == JSON_STR else value
        for key, value in py_obj.model_dump().items()
    }
    return flat_model(**flat_dict)


def from_flat_model[T: pydantic.BaseModel](flat_obj: pydantic.BaseModel, py_model: Type[T]) -> T:
    """
    Converts flat_obj to a py_model and returns the new instance.
    When the source field has JSON_STR field description, the target field is loaded and built from the source json string field.
    """
    assert isinstance(flat_obj, pydantic.BaseModel)
    py_dict: dict[str, Any] = {}
    for field_name, py_field_info in py_model.model_fields.items():
        flat_field = getattr(flat_obj, field_name, None)
        if flat_field is None:
            continue
        if flat_obj.model_fields[field_name].description == JSON_STR:
            py_dict[field_name] = _build_field_model(py_model, field_name).model_validate_json(flat_field).root
        else:
            py_dict[field_name] = flat_field
    return py_model(**py_dict)


def _build_field_model(py_model: type[pydantic.BaseModel], field_name: str) -> type[pydantic.RootModel]:
    return pydantic.RootModel[py_model.model_fields[field_name].annotation]
