from typing import Protocol, TypeAlias


PrimaryKey: TypeAlias = str
"a UUID str that is used as a primary key"


class HasPrimaryKey(Protocol):
    @property
    def pk(self) -> str:
        ...


class WithPrimaryKeyProperty:
    def __init_subclass__(cls):
        primary_key_field = None

        for field_name, annotation in cls.__annotations__.items():
            ann_str = str(annotation)
            # 1. Direct match with the TypeAlias if preserved
            # 2. Variable name heuristic as fallback
            is_pk = (
                "PrimaryKey" in ann_str 
                or ann_str.endswith(".PrimaryKey")
                or field_name.endswith("_id")
                or field_name == "pk"
            )
            
            if is_pk:
                if primary_key_field is None:
                    primary_key_field = field_name
                else:
                    # Avoid double picking if multiple _id fields exist
                    # The first one defined (Top of Class) is the formal PK
                    continue

        if primary_key_field is None:
            raise ValueError("no primary key specified")

        cls.primary_key_field = primary_key_field

    @property
    def pk(self) -> str:
        return getattr(self, self.primary_key_field)
