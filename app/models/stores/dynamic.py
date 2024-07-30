from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import registry
from sqlalchemy import (
    UUID,
    Boolean,
    Date,
    TIMESTAMP,
    Enum,
    Float,
    Integer,
    String,
    Table as SQLAlchemyTable,
    Column as SQLAlchemyColumn,
)
from sqlalchemy.dialects.postgresql import ENUM as PostgreSQLEnum
from app.models.application.base import DataType, PrimaryKey, Table

# Create a registry
mapper_registry = registry()
Base = declarative_base()

# Cache to store created ORM classes
orm_class_cache = {}


def create_dynamic_orm(table: Table, application_name: str):
    table_name = f"{application_name}_{table.name}"
    class_name = f"{table_name}_class"

    # Check if the class already exists in the cache
    if class_name in orm_class_cache:
        return orm_class_cache[class_name]

    # Create the SQLAlchemy Table object
    columns: SQLAlchemyColumn = []
    match table.primary_key:
        case PrimaryKey.AUTO_INCREMENT:
            columns.append(
                SQLAlchemyColumn(
                    "id",
                    Integer,
                    primary_key=True,
                    autoincrement=True,
                )
            )
        case PrimaryKey.UUID:
            columns.append(
                SQLAlchemyColumn(
                    "id",
                    UUID,
                    primary_key=True,
                    server_default="gen_random_uuid()",
                )
            )
        case _:
            raise ValueError(f"Unsupported primary key type: {table.primary_key}")

    for col in table.columns:
        sql_alchemy_type = _get_sqlalchemy_type(data_type=col.data_type)
        if sql_alchemy_type == Enum:
            enum_name = f"{table_name}_{col.name}_enum"
            enum_values = tuple(col.enum_values)
            sql_alchemy_type = PostgreSQLEnum(
                *enum_values, name=enum_name, create_type=False
            )
        columns.append(
            SQLAlchemyColumn(
                col.name,
                sql_alchemy_type,
            )
        )

    sqlalchemy_table = SQLAlchemyTable(
        table_name,
        mapper_registry.metadata,
        *columns,
        extend_existing=True,  # This allows redefining tables if they already exist in the metadata
    )

    # Create the ORM class
    orm_class = type(
        class_name,
        (Base,),
        {
            "__table__": sqlalchemy_table,
            "__tablename__": table_name,
        },
    )

    # Map the class to the table only if it hasn't been mapped before
    if not hasattr(orm_class, "__mapper__"):
        mapper_registry.map_imperatively(orm_class, sqlalchemy_table)

    # Cache the created class
    orm_class_cache[class_name] = orm_class

    return orm_class


def _get_sqlalchemy_type(data_type: DataType):
    return {
        DataType.STRING: String,
        DataType.INTEGER: Integer,
        DataType.FLOAT: Float,
        DataType.BOOLEAN: Boolean,
        DataType.DATE: Date,
        DataType.DATETIME: TIMESTAMP(timezone=True),
        DataType.UUID: UUID,
        DataType.ENUM: Enum,
    }.get(data_type, String)
