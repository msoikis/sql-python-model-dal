import enum
import uuid
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import pydantic
import pytest
from sqlmodel import Field

from pydantic_db_model.src.pydantic_db_model import pydantic_to_db_model, db_model_to_pydantic, generate_db_model


class BasicTypesModel(pydantic.BaseModel):
    i: int | None = Field(default=1, primary_key=True)
    b: bool = False
    f: Optional[float]
    s: str = "$$$"
    by: Optional[bytes] = None


class MyStrEnum(enum.StrEnum):
    a = "a"
    b = "b"
    c = "c"


class MyIntEnum(enum.Enum):
    a1 = 1
    a2 = 2


class SupportedExtraTypesModel(pydantic.BaseModel):
    dt: Optional[datetime] = Field(primary_key=True)
    uu: uuid.UUID = uuid.uuid4()
    ie: MyIntEnum = MyIntEnum.a2
    se: Optional[MyStrEnum] = None


class CollectionTypesModel(pydantic.BaseModel):
    key: Optional[int] = Field(default=None, primary_key=True)
    s: set[MyIntEnum]
    l: list[list[Optional[int]]] = [[1, None], [0, 3]]
    d: dict[uuid.UUID, bool] = {uuid.uuid4(): True}


class NestedPydanticModel(pydantic.BaseModel):
    key: Optional[int] = Field(default=None, primary_key=True)
    btm: BasicTypesModel = BasicTypesModel(f=0)
    d: dict[str, CollectionTypesModel] = {
        "ctm1": CollectionTypesModel(s={MyIntEnum.a1}),
        "ctm2": CollectionTypesModel(s=set()),
    }


@pytest.mark.parametrize(
    "py_obj",
    test_objects := [
        BasicTypesModel(f=0.1),
        CollectionTypesModel(s={MyIntEnum.a2}),
        NestedPydanticModel(),
        SupportedExtraTypesModel(dt=datetime.now()),
    ],
    ids=[repr(obj) for obj in test_objects]  # prints the tested objects for each case
)
def test_pydantic_db_model(py_obj: pydantic.BaseModel):
    generate_db_model(py_obj.__class__)
    print_model(py_obj.__db_model__)
    db_obj = pydantic_to_db_model(py_obj)
    print(f'\n{py_obj=}')
    print(f'{db_obj=}\n')
    converted_back_py_obj = db_model_to_pydantic(db_obj)
    assert converted_back_py_obj == py_obj


@pytest.mark.parametrize(
    "py_obj, table_name, fixed_timezone",
    test_objects := [
        (SupportedExtraTypesModel(dt=None), "table1.1", None),
        (SupportedExtraTypesModel(dt=None), "table1.2", "UTC"),
        (SupportedExtraTypesModel(dt=datetime.now()), "table1.3", None),
        (SupportedExtraTypesModel(dt=datetime.now(ZoneInfo("UTC"))), "table1.4", None),
        (SupportedExtraTypesModel(dt=datetime.now(ZoneInfo("UTC"))), "table1.5", "UTC"),
        (SupportedExtraTypesModel(dt=datetime.now(ZoneInfo("America/Los_Angeles"))), "table1.6", "UTC"),
        (SupportedExtraTypesModel(dt=datetime.now(ZoneInfo("UTC"))), "table1.7", "America/Los_Angeles"),
    ],
    ids=[f"{repr(obj)}, {timezone=}, {table_name}" for obj, table_name, timezone in test_objects]  # prints the tested objects for each case
)
def test_fixed_timezone(py_obj: pydantic.BaseModel, fixed_timezone: str, table_name: str):
    generate_db_model(py_obj.__class__, fixed_timezone, table_name)
    print_model(py_obj.__db_model__)
    db_obj = pydantic_to_db_model(py_obj)
    print(f'\n{py_obj=}')
    print(f'{db_obj=}\n')
    converted_back_py_obj = db_model_to_pydantic(db_obj)
    assert converted_back_py_obj == py_obj


@pytest.mark.parametrize(
    "py_obj, table_name, fixed_timezone",
    test_objects := [
        (SupportedExtraTypesModel(dt=datetime.now()), "table2.1", "UTC"),
    ],
    ids=[f"{repr(obj)}, {timezone=}, {table_name}" for obj, table_name, timezone in test_objects]  # prints the tested objects for each case
)
def test_conflicting_fixed_timezone(py_obj: pydantic.BaseModel, fixed_timezone: str, table_name: str):
    generate_db_model(py_obj.__class__, fixed_timezone, table_name)
    print_model(py_obj.__db_model__)
    with pytest.raises(AssertionError) as e:
        print(f'\n{py_obj=}')
        db_obj = pydantic_to_db_model(py_obj)
        print(f'{db_obj=}\n')
        converted_back_py_obj = db_model_to_pydantic(db_obj)
    print(f"{repr(e)} raised as expected")


def print_model(flat_model: type[pydantic.BaseModel]) -> None:
    print(f"\n{flat_model.__name__}: (fixed_timezone={flat_model.__fixed_timezone__})")
    for field_name, field_info in flat_model.model_fields.items():
        print(f"{field_name}: {field_info.annotation}, extra={field_info.json_schema_extra}")
