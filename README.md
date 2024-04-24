# sql-python-model-dal

This Python Repository contains two main packages: `pydantic_db_model` and `db_dal`.

## pydantic_db_model

This package solves the limitation of [SQLModel](https://sqlmodel.tiangolo.com/) & [SQLAlchemy](https://www.sqlalchemy.org/)'s ORM models which support only fields of basic python types like: str, int, float, bool and also datetime.
What if you want your model to contain also lists, dicts, other user defined subclasses?

Example of the problem:
```python
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
```

See how you can solve this problem by using the `pydantic_db_model` package in the following example:
```python
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
```

This package enables you to use Models/Classes with composite fields/properties like: lists, dicts, other pydantic.BaseModel classes.
How does it work?
The composite fields are implicitly converted to JSON strings before being stored in the database.
They are converted back to their original types when retrieved from the database. 


## db_dal

This package provides a generic DAL (Data Access Layer) Python class which contains standard CRUD (Create, Read, Update & Delete) class methods ready to use with your defined models.
Included methods: `add`, `add_list`, `get_by_key`, `get_by_dict`, `get_all`, `upsert`, `upsert_list`, `delete_record`, ` delete_by_dict`, `delete_all`, `delete_by_key`.

`db_dal` uses the `pydantic_db_model` package to support any user defined Pydantic model.

This class can be easily extended to include more specific methods for your models, for example:
```python
from datetime import datetime
from zoneinfo import ZoneInfo

import pydantic
import sqlmodel
from pydantic_db_model.src.pydantic_db_model import generate_db_model
from db_dal.src.db_engine import connect_to_db_and_create_tables
from db_dal.src.db_dal import DbDal
from pydantic_db_model.src.pydantic_to_flat.src.convert import from_flat_model


class PersonModel(pydantic.BaseModel):
    id: str = sqlmodel.Field(primary_key=True)
    name: str
    hobbies: list[str]
    created_datetime: datetime = datetime.now(ZoneInfo("UTC"))


generate_db_model(PersonModel, ZoneInfo("UTC"))


class PersonDal(DbDal):
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
            return [from_flat_model(result, self.model) for result in db_results]


if __name__ == "__main__":
    db_engine = connect_to_db_and_create_tables("sqlite:///person_example.db")
    dal = PersonDal(db_engine, PersonModel)
    dal.delete_all()
    p1 = PersonModel(id="1", name="John", hobbies=["fishing", "hiking"])
    p2 = PersonModel(id="2", name="Jane", hobbies=["swimming", "hiking"])
    dal.add_list([p1, p2])
    print(f'get by id=1: {dal.get_by_key("1")}')
    print(f'Hiking: {dal.get_by_hobby("hiking")}')
    print(f'Swimming: {dal.get_by_hobby("swimming")}')
    print(f'Flying: {dal.get_by_hobby("flying")}')
```


