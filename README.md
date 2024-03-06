# sql-python-model-dal

DAL (Data Access Layer) for SQL databases in Python, 
with support for any pydantic.BaseModel Python class. 
Classes with composite fields/properties like: lists, dicts, other pydantic.BaseModel classes,
are implicitly converted to JSON strings before being stored in the database.
They are converted back to their original types when retrieved from the database. 
