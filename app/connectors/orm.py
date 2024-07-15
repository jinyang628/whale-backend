from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import or_, and_, select, delete, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from dotenv import find_dotenv, load_dotenv
import os
from sqlalchemy.dialects.postgresql import ENUM as PostgreSQLEnum

import logging
from typing import Any, Type

from app.models.stores.base import BaseObject

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
INTERNAL_DATABASE_URL = os.environ.get("INTERNAL_DATABASE_URL")
EXTERNAL_DATABASE_URL = os.environ.get("EXTERNAL_DATABASE_URL")

class Orm:
    def __init__(
        self, 
        is_user_facing: bool = True
    ):
        self.engine = create_async_engine(
            url=EXTERNAL_DATABASE_URL if is_user_facing else INTERNAL_DATABASE_URL,
            echo=False,
        )
        self.sessionmaker = sessionmaker(
            bind=self.engine,
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        
    async def post(self, model: Type[DeclarativeMeta], data: list[dict[str, Any]]) -> tuple[list[Any], list[dict[str, Any]]]:
        """
        Inserts a list of model instances into the database.

        Parameters:
        models (list[FishBaseObject]): A list of FishBaseObject to be inserted.
        """
        orm_instances = [model(**item) for item in data]
        inserted_ids: list[Any] = []
        inserted_rows: list[dict[str, Any]] = []

        async with self.sessionmaker() as session:
            session.add_all(orm_instances)
            await session.flush()            
            inserted_ids = [instance.id for instance in orm_instances]

            # Fetch column names directly from the database
            table_name = model.__tablename__
            columns_query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name = :table_name")
            result = await session.execute(columns_query, {'table_name': table_name})
            columns = [row[0] for row in result]
            
            # Construct a query to select all columns for the inserted rows
            columns_str = ', '.join(columns)
            select_query = text(f"SELECT {columns_str} FROM {table_name} WHERE id = ANY(:ids)")
            result = await session.execute(select_query, {'ids': inserted_ids})
            
            for row in result:
                row_dict = {}
                for column, value in zip(columns, row):
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[column] = value
                inserted_rows.append(row_dict)
                logging.info(f"Inserted row: {row_dict}")
                
            await session.commit()
            log.info(f"Inserted {len(data)} rows into {model.__tablename__}")
        return inserted_ids, inserted_rows
        
    async def get_application(
        self, 
        orm_model: Type[DeclarativeMeta], 
        pydantic_model: Type[BaseModel],
        names: list[str], 
    ) -> list[BaseObject]:
        """Fetches entries from the specified table based on the filters provided.

        Args:
            orm_model (Type[DeclarativeMeta]): The SQLAlchemy ORM model to fetch data of.
            pydantic_model (Type[BaseModel]): The pydantic model to validate the ORM model to.
            filters (list[dict): The filters to apply to the query.

        Returns:
            list[FishBaseObject]: A list of FishBaseObject that match the filters.
        """
        results = []
        async with self.sessionmaker() as session:
            query = select(orm_model)
            if names:
                query_filter = or_(*[orm_model.name == name for name in names])
                query = query.filter(query_filter)                

            results = await session.execute(query)
            results = results.scalars().all()
        
        if not results:
            return []
        
        return [pydantic_model.model_validate(result) for result in results]
    
    async def get_inference_result(
        self, 
        model: Type[DeclarativeMeta], 
        filters: dict[str, Any], 
        is_and: bool = True, 
        batch_size: int = 6500
    ) -> list[dict[str, Any]]:
        """Fetches entries from the specified table based on the filters provided.

        Args:
            orm_model (Type[DeclarativeMeta]): The SQLAlchemy ORM model to fetch data of.
            pydantic_model (Type[BaseModel]): The pydantic model to validate the ORM model to.
            filters (list[dict): The filters to apply to the query.
            is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True (AND condition).

        Returns:
            list[FishBaseObject]: A list of FishBaseObject that match the filters.
        """
        results = []
        offset = 0
        
        async with self.sessionmaker() as session:
            while True:
                query = select(model)
                if filters:
                    condition = and_ if is_and else or_                        
                    query_filter = condition(*[getattr(model, column_name) == column_value for column_name, column_value in filters.items()])
                    query = query.filter(query_filter)
                
                query = query.limit(batch_size).offset(offset)
                batch_results = await session.execute(query)
                batch_results = batch_results.scalars().all()  # Add this line

                if not batch_results:
                    break
                
                results.extend(batch_results)
                offset += batch_size        
                log.info(f"Fetching {results} from database")
        
        if not results:
            return []
        
        inference_results: list[dict[str, Any]] = []
        for result in results:
            row_result = {}
            for column in result.__table__.columns:
                row_result[column.name] = getattr(result, column.name)
            inference_results.append(row_result)
        return inference_results

    
    async def delete_inference_result(
        self, 
        model: Type[DeclarativeMeta], 
        filter_conditions: list[dict[str, str]], 
        is_and: bool = True,
    ) -> list[dict[Any, dict]]:
        """Deletes entries from the specified table based on the filters provided.

        Args:
            model (Type[DeclarativeMeta]): The SQLAlchemy model to delete data of.
            filter_conditions (list[dict]): The filters to apply to the query.
            is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True.

        Returns:
            list[dict[Any, dict]]: The data necessary to reverse the deletion.
        """
        results: list[dict[str, Any]] = []
    
        async with self.sessionmaker() as session:
            condition = and_ if is_and else or_
            query_filter = condition(*[
                getattr(model, filter_dict['column_name']) == 
                _convert_value_to_column_type(model, filter_dict['column_name'], filter_dict['column_value'])
                for filter_dict in filter_conditions
            ])
            
            # Fetch the rows to be deleted
            select_stmt = select(model).where(query_filter)
            result = await session.execute(select_stmt)
            to_delete_rows = result.scalars().all()
            
            # Convert the to-be-deleted rows to dictionaries
            for row in to_delete_rows:
                row_dict = {column.name: getattr(row, column.name) for column in model.__table__.columns}
                results.append(row_dict)
            
            # Perform the delete operation
            delete_stmt = delete(model).where(query_filter)
            await session.execute(delete_stmt)
            await session.commit()
            
            log.info(f"Deleted {len(results)} rows from database")
        
        return results
    
    async def update_inference_result(
        self, 
        model: Type[DeclarativeMeta], 
        filters: dict[str, Any], 
        updated_data: dict[str, Any], 
        is_and: bool = True
    ) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
        """Updates entries in the specified table based on the filters provided.

        Args:
            model (Type[DeclarativeMeta]): The SQLAlchemy model to update data of.
            filters (dict): The filters to apply to the query.
            updated_data (dict): The updates to apply to the target rows.
            is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True.

        Returns:
            tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]: 
            A tuple containing:
            1. The updated rows
            2. The data necessary to reverse the update
        """
        
        updated_results: list[dict[str, Any]] = []
        original_results: list[dict[str, Any]] = []
        reverse_filters: list[dict[str, str]] = []
        
        async with self.sessionmaker() as session:
            condition = and_ if is_and else or_
            query_filter = condition(*[getattr(model, column_name) == column_value for column_name, column_value in filters.items()])
            
            # Fetch the original rows before update
            select_stmt = select(model).where(query_filter)
            result = await session.execute(select_stmt)
            original_rows = result.scalars().all()
            
            # Store original values and create filter conditions
            for row in original_rows:
                original_dict = {column.name: getattr(row, column.name) for column in model.__table__.columns}
                original_results.append(original_dict)
                reverse_filters.append({"id": row.id})
            
            # Perform the update
            update_values = {key: value for key, value in updated_data.items()}
            update_stmt = update(model).where(query_filter).values(**update_values)
            await session.execute(update_stmt)
            await session.commit()
            
            # Fetch the updated rows
            result = await session.execute(select_stmt)
            updated_rows = result.scalars().all()
            
            # Convert the updated rows to dictionaries
            for row in updated_rows:
                row_dict = {column.name: getattr(row, column.name) for column in model.__table__.columns}
                updated_results.append(row_dict)
            
            log.info(f"Updated {len(updated_results)} rows in database")
        
        # Create reverse updated_data
        reverse_updated_data = []
        for original, updated in zip(original_results, updated_results):
            for key, value in updated.items():
                if original[key] != value:
                    reverse_updated_data.append({key: original[key]})
        return updated_results, reverse_filters, reverse_updated_data
    
    ### Miscellaneous ###
    def get_column(self, model: Type[DeclarativeMeta], column: str, filters: dict, is_and: bool = True, batch_size: int = 6500) -> list[Any]:
        """Fetches specific columns from the specified table based on the filters provided.

        Args:
            model (Type[DeclarativeMeta]): The SQLAlchemy model to fetch data from.
            columns (str): The column name to fetch
            filters (dict): The filters to apply to the query.
            is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True (AND condition).

        Returns:
            list[Any]: A list of tuples where each tuple contains the values of the requested columns.
        """
        results = []
        offset = 0
        
        with Session(self.engine) as session:
            while True:
                query = select(getattr(model, column)) 
                if filters:
                    conditions = []
                    for key, value in filters.items():
                        attribute = getattr(model, key)
                        if isinstance(value, list) and value:
                            conditions.append(attribute.in_(value))
                        else:
                            conditions.append(attribute == value)
                    condition = and_ if is_and else or_
                    query = query.filter(condition(*conditions))

                query = query.limit(batch_size).offset(offset)
                batch_results = session.execute(query).scalars().all()

                if not batch_results:
                    break
                
                results.extend(batch_results)
                offset += batch_size
        return results 

def _convert_value_to_column_type(model, column_name, value):
    column = getattr(model, column_name)
    if isinstance(column.type, PostgreSQLEnum):
        return column.type.enum_class(value)
    return value

# TODO: Integrate this? But probably better to have a pydantic model to handle this. Boolean clause class?
def _build_filter_condition(self, model: Type[DeclarativeMeta], filters: dict[str, Any]):
    """Recursively builds complex filter conditions."""
    conditions = []
    for key, value in filters.items():
        if key.lower() == 'or':
            conditions.append(or_(*[_build_filter_condition(model, sub_filter) for sub_filter in value]))
        elif key.lower() == 'and':
            conditions.append(and_(*[_build_filter_condition(model, sub_filter) for sub_filter in value]))
        else:
            attribute = getattr(model, key)
            if isinstance(value, list):
                conditions.append(attribute.in_(value))
            else:
                conditions.append(attribute == value)
    
    return and_(*conditions) if len(conditions) > 1 else conditions[0]
