from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import pydantic
import sqlmodel
from sqlalchemy import Column, TIMESTAMP, text
from sqlmodel import Field

from pydantic_to_flat.src import convert
from sql_dal.src.db_engine import connect_to_db_and_create_tables
from sql_dal.src.generate_db_model import generate_db_model
from sql_dal.src.sql_dal import SqlDal


class PersonModel(pydantic.BaseModel):
    id: str = sqlmodel.Field(primary_key=True)
    name: str
    dt1: datetime
    hobbies: list[str]
    created_datetime: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=True,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
        default=None,
    )
    # updated_datetime: Optional[datetime] = Field(sa_column=Column(
    #     TIMESTAMP(timezone=True),
    #     nullable=False,
    #     server_default=text("CURRENT_TIMESTAMP"),
    #     server_onupdate=text("CURRENT_TIMESTAMP"),
    # ))


generate_db_model(PersonModel)


class PersonDal(SqlDal):
    def get_by_hobby(self, hobby: str) -> list[PersonModel]:
        """
        Example for a query filter:
        The desired result is to filter for a specific hobby in a list of hobbies.
        Because the hobbies field is flattened to a JSON string,
        the same result is gained by checking for the hobby substring in the hobbies JSON string.
        """
        with sqlmodel.Session(self.db_engine) as session:
            db_model = self.model.__db_model__
            statement = sqlmodel.select(db_model).where(db_model.hobbies.contains(f'"{hobby}"'))
            db_results = session.exec(statement).all()
            return [convert.from_flat_model(result, self.model) for result in db_results]


if __name__ == "__main__":
    db_engine = connect_to_db_and_create_tables("sqlite:///person_example.db")
    dal = PersonDal(db_engine, PersonModel)
    dal.delete_all()
    p1 = PersonModel(id="1", name="John", dt1=datetime.now(tz=ZoneInfo("UTC")), created_datetime=datetime(2020, 1, 1, 10, 20, tzinfo=ZoneInfo("Israel")), hobbies=["fishing", "hiking"])
    print(f"{p1.dt1=}")
    # p2 = PersonModel(id="2", name="Jane", birth_date=datetime.date(1991, 1, 1), hobbies=["swimming", "hiking"])
    dal.add_list([p1])
    pp = dal.get_by_hobby("fishing")
    # print(pp)
    p2 = pp[0]
    print(f"{p2.dt1=}")
    print(f"{p2.dt1.replace(tzinfo=ZoneInfo("Israel"))=}")
    print(f"{p2.dt1.astimezone(ZoneInfo("Israel"))=}")




    # print(f'Hiking: {dal.get_by_hobby("hiking")}')
    # print(f'Swimming: {dal.get_by_hobby("swimming")}')
    # print(f'Flying: {dal.get_by_hobby("flying")}')
