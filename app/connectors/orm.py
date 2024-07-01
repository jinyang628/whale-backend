from sqlalchemy import or_, and_, select, delete, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

import logging
from typing import Any, Type, Union

from app.models.stores.base import BaseObject
from app.models.stores.application import Application, ApplicationORM

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
        
        
    async def insert(self, model: Type[DeclarativeMeta], data: list[dict[str, Any]]) -> Any:
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
        
#     # TODO: Implement more sophisticated filter conditions -> (A OR B) AND C
#     def get(
#         self, 
#         model: Type[DeclarativeMeta], 
#         filters: dict[str, Union[list, str]], 
#         is_and: bool = True, 
#         batch_size: int = 6500
#     ) -> list[BaseObject]:
#         """Fetches entries from the specified table based on the filters provided.

#         Args:
#             model (Type[DeclarativeMeta]): The SQLAlchemy model to fetch data of.
#             filters (dict): The filters to apply to the query.
#             is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True (AND condition).

#         Returns:
#             list[FishBaseObject]: A list of FishBaseObject that match the filters.
#         """
#         results = []
#         offset = 0
        
#         with Session(self.engine) as session:
#             while True:
#                 query = select(model)
#                 if filters:
#                     conditions = []
#                     for key, value in filters.items():
#                         attribute = getattr(model, key)
#                         if isinstance(value, list) and value:
#                             conditions.append(attribute.in_(value))  # Use `in_` for lists
#                         else:
#                             conditions.append(attribute == value)  # Regular equality for single values
#                     condition = and_ if is_and else or_
#                     query = query.filter(condition(*conditions))
                
#                 query = query.limit(batch_size).offset(offset)
#                 batch_results = session.execute(query).scalars().all()

#                 if not batch_results:
#                     break
                
#                 results.extend(batch_results)
#                 offset += batch_size        
#                 log.info(f"Fetching {results} from database")
        
#         if not results:
#             return []
        
#         result: Type[DeclarativeMeta] = results[0]
#         match result:
#             case _ if isinstance(result, ApplicationORM):
#                 return [Application.model_validate(entry) for entry in results]
#             case _:
#                 raise ValueError(f"Model type {type(model)} not supported")
    
#     # TODO: Implement more sophisticated filter conditions -> (A OR B) AND C
#     def delete(
#         self, 
#         model: Type[DeclarativeMeta], 
#         filters: dict[str, Union[list, str]], 
#         is_and: bool = True
#     ) -> int:
#         """Deletes entries from the specified table based on the filters provided.

#         Args:
#             model (Type[DeclarativeMeta]): The SQLAlchemy model to delete data of.
#             filters (dict): The filters to apply to the query.
#             is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True.

#         Returns:
#             int: The number of rows deleted.
#         """
#         delete_count: int = 0
#         with Session(self.engine) as session:
#             if filters:
#                 condition = and_ if is_and else or_
#                 delete_query = delete(model).where(condition(*[getattr(model, key) == value for key, value in filters.items()]))
#                 result = session.execute(delete_query)
#                 session.commit()
#                 delete_count = result.rowcount
#         log.info(f"Deleting {delete_count} rows from database")
#         return delete_count 
    
#     # TODO: Implement more sophisticated filter conditions -> (A OR B) AND C
#     def update(
#         self, 
#         model: Type[DeclarativeMeta], 
#         filters: dict[str, Union[list, str]], 
#         updates: dict, 
#         is_and: bool = True
#     ) -> int:
#         """Updates entries in the specified table based on the filters provided.

#         Args:
#             model (Type[DeclarativeMeta]): The SQLAlchemy model to update data of.
#             filters (dict): The filters to apply to the query.
#             updates (dict): The updates to apply to the target rows.
#             is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True.

#         Returns:
#             int: The number of rows updated
#         """
#         update_count: int = 0
#         with Session(self.engine) as session:
#             condition = and_ if is_and else or_
#             query_filter = condition(*[getattr(model, key) == value for key, value in filters.items()])
#             update_stmt = update(model).where(query_filter).values(**updates)
#             result = session.execute(update_stmt)
#             session.commit()
#             update_count = result.rowcount
#         log.info(f"Updating {update_count} rows in database")
#         return update_count
    
#     ### Miscellaneous ###
#     def get_column(self, model: Type[DeclarativeMeta], column: str, filters: dict, is_and: bool = True, batch_size: int = 6500) -> list[Any]:
#         """Fetches specific columns from the specified table based on the filters provided.

#         Args:
#             model (Type[DeclarativeMeta]): The SQLAlchemy model to fetch data from.
#             columns (str): The column name to fetch
#             filters (dict): The filters to apply to the query.
#             is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True (AND condition).

#         Returns:
#             list[Any]: A list of tuples where each tuple contains the values of the requested columns.
#         """
#         results = []
#         offset = 0
        
#         with Session(self.engine) as session:
#             while True:
#                 query = select(getattr(model, column)) 
#                 if filters:
#                     conditions = []
#                     for key, value in filters.items():
#                         attribute = getattr(model, key)
#                         if isinstance(value, list) and value:
#                             conditions.append(attribute.in_(value))
#                         else:
#                             conditions.append(attribute == value)
#                     condition = and_ if is_and else or_
#                     query = query.filter(condition(*conditions))

#                 query = query.limit(batch_size).offset(offset)
#                 batch_results = session.execute(query).scalars().all()

#                 if not batch_results:
#                     break
                
#                 results.extend(batch_results)
#                 offset += batch_size
#         return results 

# # TODO: Integrate this? But probably better to have a pydantic model to handle this. Boolean clause class?
# def _build_filter_condition(self, model: Type[DeclarativeMeta], filters: dict[str, Any]):
#     """Recursively builds complex filter conditions."""
#     conditions = []
#     for key, value in filters.items():
#         if key.lower() == 'or':
#             conditions.append(or_(*[_build_filter_condition(model, sub_filter) for sub_filter in value]))
#         elif key.lower() == 'and':
#             conditions.append(and_(*[_build_filter_condition(model, sub_filter) for sub_filter in value]))
#         else:
#             attribute = getattr(model, key)
#             if isinstance(value, list):
#                 conditions.append(attribute.in_(value))
#             else:
#                 conditions.append(attribute == value)
    
#     return and_(*conditions) if len(conditions) > 1 else conditions[0]
