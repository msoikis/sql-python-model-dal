from datetime import datetime
from enum import StrEnum
from typing import Optional
from zoneinfo import ZoneInfo

import pydantic
import pytest
import sqlmodel
from sqlalchemy.exc import IntegrityError

from db_dal.src.db_dal import DbDal, DalKeyNotFoundError
from db_dal.src.db_engine import connect_to_db_and_create_tables
from pydantic_db_model.pydantic_db_model import generate_db_model

FIRST_AUTO_INT_INDEX = 1


class MyEnum(StrEnum):
    a1 = "a1"
    a2 = "a2"


class HelperStruct(pydantic.BaseModel):
    dt: datetime = datetime.now(ZoneInfo("UTC"))
    e: Optional[MyEnum] = None


class Model(pydantic.BaseModel):
    index: Optional[int] = sqlmodel.Field(default=None, primary_key=True)
    d: dict[int, HelperStruct] = {0: HelperStruct()}
    desc: Optional[str] = None


generate_db_model(Model, fixed_timezone="UTC")


@pytest.fixture
def dal() -> DbDal:
    db_engine = connect_to_db_and_create_tables("sqlite:///:memory:")
    return DbDal(db_engine, Model)


def test_get_all_empty(dal: DbDal) -> None:
    assert dal.get_all() == []


def test_add_get_all(dal: DbDal) -> None:
    tm_list = [Model(index=1), Model(index=2)]
    dal.add_list(tm_list)
    read_tms = dal.get_all()
    assert read_tms == tm_list


def test_add_get_by_key(dal: DbDal) -> None:
    tm = Model()
    dal.add(tm)
    read_tm = dal.get_by_key(FIRST_AUTO_INT_INDEX)
    tm.index = FIRST_AUTO_INT_INDEX
    assert read_tm == tm


def test_get_not_found(dal: DbDal) -> None:
    with pytest.raises(DalKeyNotFoundError) as e:
        dal.get_by_key(FIRST_AUTO_INT_INDEX)
    print(f"\n{repr(e)} raised as expected")


def test_get_by_dict(dal: DbDal) -> None:
    tm1 = Model(index=1, desc="11")
    tm2 = Model(index=2, desc="22")
    dal.add_list([tm1, tm2])
    assert dal.get_by_dict({"desc": "22", "index": 2}) == [tm2]
    assert dal.get_by_dict({"index": 1, "desc": "22"}) == []
    assert dal.get_by_dict({"d": "?"}) == []
    assert dal.get_by_dict({}) == [tm1, tm2]


def test_add_duplicate_key(dal: DbDal) -> None:
    tm1 = Model(index=1, desc="11")
    tm2 = Model(index=1, desc="22")
    with pytest.raises(IntegrityError):
        dal.add_list([tm1, tm2])
    assert dal.get_all() == []


def test_upsert(dal: DbDal) -> None:
    tm1 = Model(index=1, desc="11")
    tm2 = Model(index=2, desc="22")
    dal.add_list([tm1, tm2])
    tm3 = Model(index=2, desc="33")
    dal.upsert(tm3)
    assert dal.get_by_key(2) == tm3
    assert dal.get_all() == [tm1, tm3]
    tm4 = Model(index=4, desc="44")
    dal.upsert(tm4)
    assert dal.get_all() == [tm1, tm3, tm4]


def test_upsert_list(dal: DbDal) -> None:
    tm1 = Model(index=1, desc="11")
    tm2 = Model(index=2, desc="22")
    dal.add_list([tm1, tm2])
    tm3 = Model(index=2, desc="33")
    tm4 = Model(index=4, desc="44")
    dal.upsert_list([tm3, tm4])
    assert dal.get_all() == [tm1, tm3, tm4]
    tm5 = Model(index=5, desc="55")
    dal.upsert_list([tm5])
    assert dal.get_all() == [tm1, tm3, tm4, tm5]


def test_delete_by_dict(dal: DbDal) -> None:
    tm1 = Model(index=1, desc="11")
    tm2 = Model(index=2, desc="22")
    dal.add_list([tm1, tm2])
    dal.delete_by_dict({"desc": "22"})
    assert dal.get_all() == [tm1]
    dal.delete_by_dict({})
    assert dal.get_all() == []


def test_delete_all(dal: DbDal) -> None:
    tm1 = Model(index=1, desc="11")
    tm2 = Model(index=2, desc="22")
    dal.add_list([tm1, tm2])
    dal.delete_all()
    assert dal.get_all() == []
