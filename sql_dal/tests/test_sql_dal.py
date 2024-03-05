from datetime import datetime
from enum import StrEnum
from typing import Optional

import pydantic
import pytest
import sqlmodel

from sql_dal.src.sql_dal import Dal, DalKeyNotFoundError
from sql_dal.src.db_engine import connect_to_db_and_create_tables
from sql_dal.src.link_to_db_model import generate_db_model

FIRST_AUTO_INT_INDEX = 1


class MyEnum(StrEnum):
    a1 = "a1"
    a2 = "a2"


class HelperStruct(pydantic.BaseModel):
    dt: datetime = datetime.now()
    e: Optional[MyEnum] = None


# @link_to_db_model
class TestModel(pydantic.BaseModel):
    index: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    d: dict[int, HelperStruct] = {0: HelperStruct()}
    desc: Optional[str] = None


TestModel.__db_model__ = generate_db_model(TestModel)


@pytest.fixture
def dal() -> Dal:
    db_engine = connect_to_db_and_create_tables("sqlite:///:memory:")
    return Dal(db_engine, TestModel)


def test_get_all_empty(dal: Dal) -> None:
    assert dal.get_all() == []


def test_add_get_all(dal: Dal) -> None:
    tm_list = [TestModel(index=1), TestModel(index=2)]
    dal.add_list(tm_list)
    read_tms = dal.get_all()
    assert read_tms == tm_list


def test_add_get_by_key(dal: Dal) -> None:
    tm = TestModel()
    dal.add(tm)
    read_tm = dal.get_by_key(FIRST_AUTO_INT_INDEX)
    tm.index = FIRST_AUTO_INT_INDEX
    assert read_tm == tm


def test_get_not_found(dal: Dal) -> None:
    with pytest.raises(DalKeyNotFoundError) as e:
        dal.get_by_key(FIRST_AUTO_INT_INDEX)
    print(f"\n{repr(e)} raised as expected")


def test_get_by_dict(dal: Dal) -> None:
    tm1 = TestModel(index=1, desc="11")
    tm2 = TestModel(index=2, desc="22")
    dal.add_list([tm1, tm2])
    assert dal.get_by_dict({"desc": "22", "index": 2}) == [tm2]
    assert dal.get_by_dict({"index": 1, "desc": "22"}) == []
    assert dal.get_by_dict({"d": "?"}) == []
