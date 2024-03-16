import pydantic
import sqlmodel
from pydantic_to_flat.src.create_flat_model import generate_flat_fields_definition_dict, \
    validate_flat_pydantic_model


def generate_db_model[T: type[pydantic.BaseModel]](cls: T, to_timezone: str = "") -> T:
    """
    This function should be called immediately after pydantic.BaseModel class definition.
    It generates a flat Pydantic SqlModel and saves it in __db_model__ class property.

    Usage example:

    class Model(pydantic.BaseModel):
        index: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
        d: dict[int, str]

    generate_db_model(Model)
    """
    cls.__db_model__ = _create_db_model(cls, to_timezone)
    return cls


def _create_db_model(cls: type[pydantic.BaseModel], to_timezone: str = "") -> type[sqlmodel.SQLModel]:
    db_model = pydantic.create_model(
        f"{cls.__name__}DbModel",
        __base__=sqlmodel.SQLModel,
        __cls_kwargs__={"table": True},
        __tablename__=cls.__name__,
        **generate_flat_fields_definition_dict(cls, to_timezone),
    )
    validate_flat_pydantic_model(db_model)
    return db_model
