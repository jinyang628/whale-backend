from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import registry
from sqlalchemy import UUID, Boolean, Date, DateTime, Float, Integer, String, Table as SQLAlchemyTable, Column as SQLAlchemyColumn

from app.models.application import DataType, PrimaryKey, Table

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
    sqlalchemy_table = SQLAlchemyTable(
        table_name, 
        mapper_registry.metadata,
        *[SQLAlchemyColumn(
            col.name,
            _get_sqlalchemy_type(col.data_type),
            primary_key=(col.primary_key != PrimaryKey.NONE),
            autoincrement=(col.primary_key == PrimaryKey.AUTO_INCREMENT),
            nullable=col.nullable
        ) for col in table.columns],
        extend_existing=True  # This allows redefining tables if they already exist in the metadata
    )

    # Create the ORM class
    orm_class = type(class_name, (Base,), {
        "__table__": sqlalchemy_table,
        "__tablename__": table_name,
    })

    # Map the class to the table only if it hasn't been mapped before
    if not hasattr(orm_class, '__mapper__'):
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
        DataType.DATETIME: DateTime,
        DataType.UUID: UUID,
    }.get(data_type, String)