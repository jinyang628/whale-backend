import json
from app.models.application import DataType, PrimaryKey, Table
from app.models.stores.base import BaseObject
from app.models.utils import generate_identifier, sql_value_to_typed_value
from sqlalchemy import Column as SQLAlchemyColumn, Integer, String, Boolean, Float
from sqlalchemy.orm import declarative_base 
from sqlalchemy.sql import func

Base = declarative_base()
        
def create_dynamic_orm(table: Table, application_name: str):
    
    table_name=f"{application_name}_{table.name}"
    
    attributes = {
        "__tablename__": table_name,
        **{
            col.name: SQLAlchemyColumn(
                _get_sqlalchemy_type(col.data_type),
                primary_key=(col.primary_key == PrimaryKey.AUTO_INCREMENT),
                autoincrement=(col.primary_key == PrimaryKey.AUTO_INCREMENT),
                nullable=col.nullable
            )
            for col in table.columns
        }
    }
    
    return type(table_name, (Base,), attributes)

# TODO: Update hte mapping when more types are allowed 
def _get_sqlalchemy_type(data_type: DataType):
    return {
        DataType.STRING: String,
        DataType.INTEGER: Integer,
        DataType.FLOAT: Float,
        DataType.BOOLEAN: Boolean,
    }.get(data_type, String)

# class DynamicORM(Base):
#     __tablename__ = "dynamic"
    
#     _DUMMY_HUGE_WHALE_ID = Column(Integer, primary_key=True)  # Dummy key
    
#     @classmethod
#     def from_pydantic(cls, table: Table, application_name: str):
#         tablename = f"{application_name}_{table.name}"
#         columns = {}
#         for column in table.columns:
#             if column.data_type == DataType.STRING:
#                 column_type = String
#             elif column.data_type == DataType.INTEGER:
#                 column_type = Integer
#             elif column.data_type == DataType.FLOAT:
#                 column_type = Float
#             elif column.data_type == DataType.BOOLEAN:
#                 column_type = Boolean
#             else:
#                 raise ValueError(f'Unsupported data type: {column.data_type}')

#             is_primary_key = column.primary_key != PrimaryKey.NONE
#             columns[column.name] = Column(column_type, nullable=column.nullable, primary_key=is_primary_key)
            
#         attributes = {
#             "__tablename__": tablename,
#             **columns
#         }
        
#         # Remove dummy primary key
#         attributes.pop('_DUMMY_HUGE_WHALE_ID', None)
        
#         new_class = type(
#             tablename,
#             (cls,),
#             attributes
#         )
        
#         return new_class
