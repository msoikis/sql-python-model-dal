from datetime import datetime
from zoneinfo import ZoneInfo

import pydantic


def verify_fixed_timezone_in_model(model_obj: pydantic.BaseModel, fixed_timezone: str) -> None:
    """
    If fixed_timezone is set, all datetime fields must have the same timezone as the fixed_timezone.
    """
    assert isinstance(model_obj, pydantic.BaseModel), f"py_obj={repr(model_obj)} must be a pydantic.BaseModel class/subclass"
    if fixed_timezone:
        for key, value in model_obj.model_dump().items():
            if isinstance(value, datetime):
                assert value.tzinfo == ZoneInfo(
                    fixed_timezone), f"datetime field ({key}={value}) must have the same timezone as the fixed_timezone ({fixed_timezone})"


def fix_missing_timezone_in_model(model_obj: pydantic.BaseModel, fixed_timezone: str) -> None:
    """
    If fixed_timezone is set, all naive (without timezone) target datetime fields are set to fixed_timezone.
    """
    assert isinstance(model_obj, pydantic.BaseModel), f"flat_obj={repr(model_obj)} must be a pydantic.BaseModel class/subclass"
    for key, value in model_obj.model_dump().items():
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=ZoneInfo(fixed_timezone))
            assert value.tzinfo == ZoneInfo(fixed_timezone), f"datetime field ({key}={value}) must have the same timezone as the fixed_timezone ({fixed_timezone})"
