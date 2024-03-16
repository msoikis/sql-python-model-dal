from zoneinfo import ZoneInfo

import pydantic
import sqlmodel
from sqlmodel import SQLModel

from pydantic_db_model.fix_missing_timezone.fix_missing_timezone import verify_fixed_timezone_in_model, fix_missing_timezone_in_model
from pydantic_db_model.pydantic_to_flat.src import convert
from pydantic_db_model.pydantic_to_flat.src.convert import from_flat_model
from pydantic_db_model.pydantic_to_flat.src import generate_flat_fields_definition_dict, \
    validate_flat_pydantic_model


def generate_db_model[T: type[pydantic.BaseModel]](cls: T, fixed_timezone: str = "") -> T:
    """
    This function should be called immediately after pydantic.BaseModel class definition.
    It generates a flat Pydantic SqlModel and saves it in __db_model__ class property.

    Usage example:

    class Model(pydantic.BaseModel):
        index: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
        d: dict[int, str]

    generate_db_model(Model)
    """
    cls.__db_model__ = _create_db_model(cls, fixed_timezone)
    return cls


def _create_db_model(cls: type[pydantic.BaseModel], fixed_timezone: str = "") -> type[sqlmodel.SQLModel]:
    db_model = pydantic.create_model(
        f"{cls.__name__}DbModel",
        __base__=sqlmodel.SQLModel,
        __cls_kwargs__={"table": True},
        __tablename__=cls.__name__,
        **generate_flat_fields_definition_dict(cls),
    )
    db_model.__fixed_timezone__ = fixed_timezone
    if fixed_timezone:
        assert ZoneInfo(fixed_timezone), f"{fixed_timezone=} must be a valid timezone, accepted by ZoneInfo()"
    validate_flat_pydantic_model(db_model)
    return db_model


def pydantic_to_db_model(py_obj: pydantic.BaseModel) -> SQLModel:
    """
    Returns a flat pydantic DB model, from py_obj
    """
    assert hasattr(py_obj, "__db_model__"), f"Use generate_db_model({py_obj.__class__.__name__}) after class definition to create and link it to a db_model"
    flat_obj = convert.to_flat_model(py_obj, py_obj.__db_model__)
    verify_fixed_timezone_in_model(flat_obj, flat_obj.__fixed_timezone__)
    return flat_obj


def db_model_to_pydantic[T: pydantic.BaseModel](db_obj: SQLModel, py_model: type[T]) -> T:
    """
    Returns a pydantic model, from db_obj
    """
    fix_missing_timezone_in_model(db_obj, db_obj.__fixed_timezone__)
    return from_flat_model(db_obj, py_model)
