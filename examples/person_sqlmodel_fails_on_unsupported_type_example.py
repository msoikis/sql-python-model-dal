from datetime import datetime
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo

import pydantic
from sqlmodel import SQLModel, Field, Session, create_engine


class Gender(str, Enum):
    male = "male"
    female = "female"
    unspecified = "unspecified"


class Child(pydantic.BaseModel):
    name: str
    gender: Gender


class PersonModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gender: Gender
    children: list[Child]  # This type list[Child] is not supported by SQLModel
    created_datetime: datetime = Field(default=datetime.now(ZoneInfo("UTC")))


if __name__ == "__main__":
    # create SQLModel table and connect to the database
    engine = create_engine("sqlite:///person_sqlmodel.db")
    SQLModel.metadata.create_all(engine)

    # Add data to DB:
    with Session(engine) as session:
        john = PersonModel(name="John", gender=Gender.male, children=[Child(name="Alice", gender=Gender.female)])
        session.add(john)
        session.commit()

    # When running this example, we get the following error:
    # ValueError: <class 'list'> has no matching SQLAlchemy type

    # Another problem: some databases, like sqlite, does not save the timezone info of datetime objects
