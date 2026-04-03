from typing import Protocol


type PrimaryKey = str
"a UUID str that is used as a primary key"


class HasPrimaryKey(Protocol):
    @property
    def pk(self) -> str:
        ...


class WithPrimaryKeyProperty:
    def __init_subclass__(cls):
        primary_key_field = None

        for field, annotation in cls.__annotations__.items():
            if str(annotation) in PrimaryKey.__name__:
                if primary_key_field is None:
                    primary_key_field = field
                else:
                    raise ValueError(f"more than one primary key specified: {primary_key_field!r} and {field!r}")

        if primary_key_field is None:
            raise ValueError("no primary key specified")

        cls.primary_key_field = primary_key_field

    @property
    def pk(self) -> str:
        return getattr(self, self.primary_key_field)
