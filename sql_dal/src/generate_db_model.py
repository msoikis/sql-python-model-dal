import pydantic
import sqlmodel
from pydantic_to_flat.src.generate_flat_fields_definition import generate_flat_fields_definition_dict, \
    validate_flat_pydantic_model, JSON_STR


def generate_db_model[T: type[pydantic.BaseModel]](cls: T) -> T:
    """
    This function should be called immediately after pydantic.BaseModel class definition.
    It generates a flat Pydantic SqlModel and saves it in __db_model__ class property.

    Usage example:

    class Model(pydantic.BaseModel):
        index: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
        d: dict[int, str]

    generate_db_model(Model)
    """
    cls.__db_model__ = _create_db_model(cls)
    return cls


def _create_db_model(cls: type[pydantic.BaseModel]) -> type[sqlmodel.SQLModel]:
    db_model = pydantic.create_model(
        f"{cls.__name__}DbModel",
        __base__=sqlmodel.SQLModel,
        __cls_kwargs__={"table": True},
        __tablename__=cls.__name__,
        **generate_flat_fields_definition_dict(cls),
    )
    validate_db_model(db_model)
    return db_model


def validate_db_model(db_model: type[pydantic.BaseModel]) -> None:
    validate_flat_pydantic_model(db_model)
    for field_info in db_model.model_fields.values():
        # JSON flat fields are not allowed, for now, to be defined as primary keys
        assert not (field_info.description == JSON_STR and hasattr(field_info, "primary_key"))
