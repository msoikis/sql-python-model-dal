import datetime

import pydantic
import sqlmodel

from pydantic_to_flat.src import convert
from sql_dal.src.db_engine import connect_to_db_and_create_tables
from sql_dal.src.generate_db_model import generate_db_model
from sql_dal.src.sql_dal import SqlDal


class PersonModel(pydantic.BaseModel):
    id: str = sqlmodel.Field(primary_key=True)
    name: str
    birth_date: datetime.date
    hobbies: list[str]


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
    p1 = PersonModel(id="1", name="John", birth_date=datetime.date(1990, 1, 1), hobbies=["fishing", "hiking"])
    p2 = PersonModel(id="2", name="Jane", birth_date=datetime.date(1991, 1, 1), hobbies=["swimming", "hiking"])
    dal.add_list([p1, p2])
    print(f'Fishing: {dal.get_by_hobby("fishing")}')
    print(f'Hiking: {dal.get_by_hobby("hiking")}')
    print(f'Swimming: {dal.get_by_hobby("swimming")}')
    print(f'Flying: {dal.get_by_hobby("flying")}')
