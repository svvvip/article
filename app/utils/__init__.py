from datetime import date, datetime
from typing import Dict, get_origin, get_args, Union


def dict_trans_obj(source: Dict, target: object):
    if not source or not target:
        return

    annotations = getattr(target, "__annotations__", None)
    if not annotations:
        return

    for name, field_type in annotations.items():
        if name not in source:
            continue

        value = source.get(name)
        if value is None:
            setattr(target, name, None)
            continue

        origin = get_origin(field_type)
        args = get_args(field_type)
        if origin is Union and len(args) == 2 and type(None) in args:
            field_type = args[0] if args[1] is type(None) else args[1]

        try:
            if field_type is date and isinstance(value, str):
                value = date.fromisoformat(value)

            elif field_type is datetime and isinstance(value, str):
                value = datetime.fromisoformat(value)

        except ValueError as e:
            raise ValueError(f"Invalid date format for field '{name}': {value}") from e

        setattr(target, name, value)