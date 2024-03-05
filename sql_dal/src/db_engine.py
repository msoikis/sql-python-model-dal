import logging

import sqlmodel
from sqlalchemy import Engine


def connect_to_db_and_create_tables(db_connection_url: str) -> Engine:
    engine = sqlmodel.create_engine(url=db_connection_url, echo=False)
    logging.debug(f"Connected to DB {db_connection_url}")
    _create_db_and_tables(engine)
    return engine


def _create_db_and_tables(db_engine: Engine):
    sqlmodel.SQLModel.metadata.create_all(db_engine)
    logging.debug("DB & Tables created! \n")
