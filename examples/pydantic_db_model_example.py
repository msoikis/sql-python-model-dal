from datetime import datetime
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo

import pydantic
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Field, Session, select

from pydantic_db_model.src.pydantic_db_model import generate_db_model, pydantic_to_db_model, db_model_to_pydantic


class Gender(str, Enum):
    male = "male"
    female = "female"
    unspecified = "unspecified"


class Child(pydantic.BaseModel):
    name: str
    gender: Gender


class PersonModel(pydantic.BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gender: Gender
    children: list[Child]
    created_datetime: datetime = Field(default=datetime.now(ZoneInfo("UTC")))


# Generates a flat Pydantic SqlModel and saves it in __db_model__ class property of PersonModel:
generate_db_model(PersonModel, ZoneInfo("UTC"))


if __name__ == "__main__":
    # create SQLModel table and connect to the database
    db_engine = create_engine("sqlite:///person_pydantic_db_model.db")
    SQLModel.metadata.create_all(db_engine)

    # Add data to DB:
    with Session(db_engine) as session:
        john = PersonModel(name="John", gender=Gender.male, children=[Child(name="Alice", gender=Gender.female)])
        # Use pydantic_to_db_model() to convert the Pydantic model to the inner SQLModel
        session.add(pydantic_to_db_model(john))
        session.commit()

    # Query the data:
    with Session(db_engine) as session:
        # Get the inner SQLModel class by the __db_model__ property
        statement = select(PersonModel.__db_model__)
        person_db_model = session.exec(statement).first()
        print(repr(person_db_model))
        # Use db_model_to_pydantic() to convert the inner SQLModel to the user defined Pydantic model
        print(repr(db_model_to_pydantic(person_db_model)))
