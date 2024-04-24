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
