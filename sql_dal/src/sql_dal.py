import logging
from typing import Any

import pydantic
import sqlmodel
from sqlalchemy import Engine

from pydantic_to_flat.src import convert
from pydantic_to_flat.src.generate_flat_fields_definition import PydanticFieldDefinition


class DalKeyNotFoundError(Exception):
    pass


class SqlDal[T: pydantic.BaseModel]:
    def __init__(self, db_engine: Engine, model: type[T]):
        self.db_engine = db_engine
        self.model = model
        assert hasattr(model, "__db_model__")
        self.key_fields = self.get_key_fields()
        if len(self.key_fields) == 1:
            self.key_field_name = list(self.key_fields.keys())[0]

    def get_key_fields(self) -> dict[str, PydanticFieldDefinition]:
        return {
            field: (info.annotation, info)
            for field, info in self.model.model_fields.items()
            if getattr(info, "primary_key", None) is not None
        }

    def get_all(self) -> list[T]:
        return self.get_by_dict({})

    def get_by_dict(self, args_dict: dict[str, Any]) -> list[T]:
        logging.debug(f"Getting records from DB filtered by {args_dict}")
        with sqlmodel.Session(self.db_engine) as session:
            statement = sqlmodel.select(self.model.__db_model__)
            for key, value in args_dict.items():
                statement = statement.where(getattr(self.model.__db_model__, key) == value)
            db_results = session.exec(statement).all()
            assert isinstance(db_results, list)
            return [convert.from_flat_model(result, self.model) for result in db_results]

    def get_by_key(self, key: ...) -> T:
        def validate_key_fields(keys_dict: dict[str, Any]) -> None:
            assert len(keys_dict) == len(self.key_fields)
            for key, value in keys_dict.items():
                assert isinstance(value, self.key_fields[key][0])

        def get_one_by_dict(keys_dict: dict[str, Any]) -> T:
            db_results = self.get_by_dict(keys_dict)
            if not db_results:
                raise DalKeyNotFoundError(f'Key {keys_dict} not found in {self.model.__db_model__.__tablename__} DB table')
            assert len(db_results) == 1
            return db_results[0]

        def get_by_keys_dict(keys_dict: dict[str, Any]) -> T:
            validate_key_fields(keys_dict)
            return get_one_by_dict(keys_dict)

        if isinstance(key, dict):
            return get_by_keys_dict(key)
        elif isinstance(key, pydantic.BaseModel):
            return get_by_keys_dict(key.model_dump())
        else:
            assert hasattr(self, "key_field_name"), f"{self.model} has no single key field defined"
            return get_by_keys_dict({self.key_field_name: key})

    def get_by_keys_list(self, keys_list: list[...]) -> list[T]:
        return [self.get_by_key(key) for key in keys_list]

    def add(self, record: T) -> None:
        logging.debug(f"Adding record to DB: {record}")
        assert isinstance(record, self.model)
        with sqlmodel.Session(self.db_engine) as session:
            session.add(convert.to_flat_model(record, record.__db_model__))
            session.commit()
        logging.debug("Record added to DB! \n")

    def add_list(self, records: list[T]) -> None:
        logging.debug(f"Adding {len(records)} records to DB:")
        with sqlmodel.Session(self.db_engine) as session:
            for record in records:
                assert isinstance(record, self.model)
                session.add(convert.to_flat_model(record, record.__db_model__))
            session.commit()
        logging.debug("Records added to DB! \n")

    def upsert(self, record: T) -> None:
        assert isinstance(record, self.model)
        with sqlmodel.Session(self.db_engine) as session:
            session.merge(convert.to_flat_model(record, record.__db_model__))
            session.commit()

    def upsert_list(self, records: list[T]) -> None:
        with sqlmodel.Session(self.db_engine) as session:
            for record in records:
                assert isinstance(record, self.model)
                session.merge(convert.to_flat_model(record, record.__db_model__))
            session.commit()

    def delete_by_dict(self, args_dict: dict) -> None:
        with sqlmodel.Session(self.db_engine) as session:
            statement = sqlmodel.delete(self.model.__db_model__)
            for key, value in args_dict.items():
                statement = statement.where(getattr(self.model.__db_model__, key) == value)
            session.exec(statement)
            session.commit()

    def delete_all(self) -> None:
        self.delete_by_dict({})

    def delete_record(self, record: T) -> None:
        assert isinstance(record, self.model)
        self.delete_by_dict(convert.to_flat_model(record, record.__db_model__))

    def delete_by_key(self, key: ...) -> None:
        if isinstance(key, dict):
            self.delete_by_dict(key)
        elif isinstance(key, pydantic.BaseModel):
            self.delete_by_dict(key.model_dump())
        else:
            assert hasattr(self, "key_field_name"), f"{self.model} has no single key field defined"
            self.delete_by_dict({self.key_field_name: key})

    def delete_by_keys_list(self, keys_list: list[...]) -> None:
        for key in keys_list:
            self.delete_by_key(key)
