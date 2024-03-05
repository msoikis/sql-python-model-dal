import enum
import uuid
from datetime import datetime
from typing import Optional

import pydantic
import pytest

from pydantic_to_flat.src import convert
from pydantic_to_flat.src.generate_flat_fields_definition import generate_flat_fields_definition_dict


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
    dt: Optional[datetime] = datetime.now()
    uu: uuid.UUID = uuid.uuid4()
    ie: MyIntEnum
    se: MyStrEnum = MyStrEnum.b


class CollectionTypesModel(pydantic.BaseModel):
    s: set[MyIntEnum]
    l: list[list[Optional[int]]] = [[1, None], [0, 3]]
    d: dict[uuid.UUID, datetime] = {uuid.uuid4(): datetime.now()}


class NestedPydanticModel(pydantic.BaseModel):
    btm: BasicTypesModel = BasicTypesModel(f=0)
    d: dict[str, CollectionTypesModel] = {
        "ctm1": CollectionTypesModel(s={MyIntEnum.a1}),
        "ctm2": CollectionTypesModel(s=set())
    }


@pytest.mark.parametrize(
    'py_obj',
    test_objects := [
        BasicTypesModel(f=0.1),
        SupportedExtraTypesModel(ie=MyIntEnum.a1),
        CollectionTypesModel(s={MyIntEnum.a2}),
        NestedPydanticModel(),
    ],
    ids=[obj.__class__.__name__ for obj in test_objects]
)
def test_pydantic_to_flat(py_obj: pydantic.BaseModel):
    flat_model = pydantic.create_model(
        f"{py_obj.__class__.__name__}FlatModel",
        **generate_flat_fields_definition_dict(py_obj.__class__),
    )
    flat_obj = convert.to_flat_model(py_obj, flat_model)
    print(f'\n{py_obj=}')
    print(f'{flat_obj=}')
    converted_back_py_obj = convert.from_flat_model(flat_obj, py_obj.__class__)
    assert converted_back_py_obj == py_obj
