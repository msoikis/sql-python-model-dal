import enum
import uuid
from datetime import datetime
from typing import Optional

import pydantic
import pytest

from pydantic_db_model.src.pydantic_to_flat.src import convert
from pydantic_db_model.src.pydantic_to_flat.src.create_flat_model import create_flat_model


class BasicTypesModel(pydantic.BaseModel):
    i: int | None = 1
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
    dt: Optional[datetime]
    uu: uuid.UUID = uuid.uuid4()
    ie: MyIntEnum = MyIntEnum.a2
    se: Optional[MyStrEnum] = None


class CollectionTypesModel(pydantic.BaseModel):
    s: set[MyIntEnum]
    l: list[list[Optional[int]]] = [[1, None], [0, 3]]
    d: dict[uuid.UUID, bool] = {uuid.uuid4(): True}


class NestedPydanticModel(pydantic.BaseModel):
    btm: BasicTypesModel = BasicTypesModel(f=0)
    d: dict[str, CollectionTypesModel] = {
        "ctm1": CollectionTypesModel(s={MyIntEnum.a1}),
        "ctm2": CollectionTypesModel(s=set())
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
def test_pydantic_to_flat(py_obj: pydantic.BaseModel):
    flat_model = create_flat_model(py_obj.__class__)
    print_model(flat_model)
    flat_obj = convert.to_flat_model(py_obj, flat_model)
    print(f'\n{py_obj=}')
    print(f'{flat_obj=}\n')
    converted_back_py_obj = convert.from_flat_model(flat_obj, py_obj.__class__)
    assert converted_back_py_obj == py_obj


def print_model(model: type[pydantic.BaseModel]) -> None:
    print(f"\n{model.__name__}:")
    for field_name, field_info in model.model_fields.items():
        print(f"{field_name}: {field_info.annotation}, extra={field_info.json_schema_extra}")

