from datetime import tzinfo
from typing import Optional

import pydantic
import sqlmodel
from sqlmodel import SQLModel

from pydantic_db_model.src.fix_missing_timezone.fix_missing_timezone import verify_datetime_fields_are_timezone_aware, set_missing_timezone_in_model
from pydantic_db_model.src.pydantic_to_flat.src import convert
from pydantic_db_model.src.pydantic_to_flat.src.convert import from_flat_model
from pydantic_db_model.src.pydantic_to_flat.src.create_flat_model import generate_flat_fields_definition_dict, \
    validate_flat_pydantic_model


def generate_db_model[T: type[pydantic.BaseModel]](cls: T, fixed_timezone: Optional[tzinfo] = None, table_name: str = "") -> T:
    """
    This function should be called immediately after pydantic.BaseModel class definition.
    It generates a flat Pydantic SqlModel and saves it in __db_model__ class property.

    Usage example:

    class Model(pydantic.BaseModel):
        index: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
        d: dict[int, str]

    generate_db_model(Model)
    """
    cls.__db_model__ = _create_db_model(cls, fixed_timezone, table_name)
    return cls


def _create_db_model(cls: type[pydantic.BaseModel], fixed_timezone: Optional[tzinfo] = None, table_name: str = "") -> type[sqlmodel.SQLModel]:
    db_model = pydantic.create_model(
        f"{cls.__name__}DbModel",
        __base__=sqlmodel.SQLModel,
        __cls_kwargs__={"table": True},
        __tablename__=table_name or cls.__name__,
        **generate_flat_fields_definition_dict(cls),
    )
    db_model.__pydantic_model__ = cls
    db_model.__fixed_timezone__ = fixed_timezone
    validate_flat_pydantic_model(db_model)
    return db_model


def pydantic_to_db_model(py_obj: pydantic.BaseModel) -> SQLModel:
    """
    Returns a flat pydantic DB model, from py_obj
    """
    assert hasattr(py_obj, "__db_model__"), f"Use generate_db_model({py_obj.__class__.__name__}) after class definition to create and link it to a db_model"
    flat_obj = convert.to_flat_model(py_obj, py_obj.__db_model__)
    if flat_obj.__fixed_timezone__:
        verify_datetime_fields_are_timezone_aware(flat_obj)
    return flat_obj


def db_model_to_pydantic(db_obj: SQLModel) -> pydantic.BaseModel:
    """
    Returns a pydantic model, from db_obj
    """
    if db_obj.__fixed_timezone__:
        set_missing_timezone_in_model(db_obj, db_obj.__fixed_timezone__)
    return from_flat_model(db_obj, db_obj.__pydantic_model__)
