from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo

import pydantic


def verify_datetime_fields_are_timezone_aware(model_obj: pydantic.BaseModel) -> None:
    """
    Verifies that all datetime fields are timezone aware (timezone defined).
    """
    assert isinstance(model_obj, pydantic.BaseModel), f"py_obj={repr(model_obj)} must be a pydantic.BaseModel class/subclass"
    for key, value in model_obj.model_dump().items():
        if isinstance(value, datetime):
            assert value.tzinfo is not None, (
                f"There is an error in {repr(model_obj)}: timezone is not defined in datetime field {key}={value}"
            )


def set_missing_timezone_in_model(model_obj: pydantic.BaseModel, fixed_timezone: tzinfo) -> None:
    """
    If fixed_timezone is set, all naive (undefined timezone) target datetime fields are set to fixed_timezone.
    """
    assert isinstance(model_obj, pydantic.BaseModel), f"flat_obj={repr(model_obj)} must be a pydantic.BaseModel class/subclass"
    for key, value in model_obj.model_dump().items():
        if isinstance(value, datetime) and value.tzinfo is None:
                value = value.replace(tzinfo=fixed_timezone)
                # TODO: check this updates the real object...
