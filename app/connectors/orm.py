from pydantic import BaseModel
from sqlalchemy import or_, and_, select, delete, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import logging
from typing import Any, Type

from app.models.stores.base import BaseObject

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class Orm:
    def __init__(
        self, 
        url: str,
    ):
        self.engine = create_async_engine(
            url,
            echo=True
        )
        self.sessionmaker = sessionmaker(
            bind=self.engine,
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        
    async def insert(self, model: Type[DeclarativeMeta], data: list[dict[str, Any]]):
        """
        Inserts a list of model instances into the database.

        Parameters:
        models (list[FishBaseObject]): A list of FishBaseObject to be inserted.
        """
        orm_instances = [model(**item) for item in data]
        async with self.sessionmaker() as session:
            session.add_all(orm_instances)
            await session.commit()
            log.info(f"Inserted {len(data)} rows into {model.__tablename__}")
        
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
        orm_model: Type[DeclarativeMeta], 
        filters: list[dict[str, str]], 
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
                query = select(orm_model)
                if filters:
                    condition = and_ if is_and else or_                        
                    query_filter = condition(*[getattr(orm_model, filter_dict['column_name']) == filter_dict['column_value'] for filter_dict in filters])
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
            for column in result.__table__.columns:
                inference_results.append({column.name: getattr(result, column.name)})
        return inference_results

    
    async def delete_inference_result(
        self, 
        model: Type[DeclarativeMeta], 
        filter_conditions: list[dict[str, str]], 
        is_and: bool = True,
    ) -> int:
        """Deletes entries from the specified table based on the filters provided.

        Args:
            model (Type[DeclarativeMeta]): The SQLAlchemy model to delete data of.
            filter_conditions (list[dict]): The filters to apply to the query.
            is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True.

        Returns:
            int: The number of rows deleted.
        """
        results: list[dict[str, Any]] = []
    
        async with self.sessionmaker() as session:
            condition = and_ if is_and else or_
            query_filter = condition(*[getattr(model, filter_dict['column_name']) == filter_dict['column_value'] for filter_dict in filter_conditions])
            
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
        filter_conditions: list[dict[str, str]], 
        updated_data: list[dict[str, Any]], 
        is_and: bool = True
    ) -> list[dict[str, Any]]:
        """Updates entries in the specified table based on the filters provided.

        Args:
            model (Type[DeclarativeMeta]): The SQLAlchemy model to update data of.
            filters (list[dict]): The filters to apply to the query.
            updates (list[dict]): The updates to apply to the target rows.
            is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True.

        Returns:
            list[dict[str, Any]]: The updated rows
        """
        
        results: list[dict[str, Any]] = []
        
        async with self.sessionmaker() as session:
            condition = and_ if is_and else or_
            query_filter = condition(*[getattr(model, filter_dict['column_name']) == filter_dict['column_value'] for filter_dict in filter_conditions])
            update_values = {item['column_name']: item['column_value'] for item in updated_data}
            update_stmt = update(model).where(query_filter).values(**update_values)
            result = await session.execute(update_stmt)
            await session.commit()
            
            # Fetch the updated rows
            select_stmt = select(model).where(query_filter)
            result = await session.execute(select_stmt)
            updated_rows = result.scalars().all()
            
            # Convert the updated rows to dictionaries
            for row in updated_rows:
                row_dict = {column.name: getattr(row, column.name) for column in model.__table__.columns}
                results.append(row_dict)
            
            log.info(f"Updated {len(results)} rows in database")
            
        return results
    
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
