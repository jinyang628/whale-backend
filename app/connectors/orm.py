from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import BinaryExpression, column, or_, and_, select, delete, true, update
from asyncpg.pgproto.pgproto import UUID as AsyncpgUUID
from sqlalchemy.orm import Session, sessionmaker, aliased
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from dotenv import find_dotenv, load_dotenv
import os

import logging
from typing import Any, Optional, Type

from app.models.stores.base import BaseObject

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
INTERNAL_DATABASE_URL = os.environ.get("INTERNAL_DATABASE_URL")
EXTERNAL_DATABASE_URL = os.environ.get("EXTERNAL_DATABASE_URL")


# All these functions work but are an absolute mess implementation wise. Please refactor. But lets get to it after the structure of the filter conditions and everything is firmed.
class Orm:
    def __init__(self, is_user_facing: bool = True):
        self.engine = create_async_engine(
            url=EXTERNAL_DATABASE_URL if is_user_facing else INTERNAL_DATABASE_URL,
            echo=False,
        )
        self.sessionmaker = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def post(
        self, model: Type[DeclarativeMeta], data: list[dict[str, Any]]
    ) -> tuple[list[Any], list[dict[str, Any]]]:
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
            for instance in orm_instances:
                if isinstance(instance.id, AsyncpgUUID):
                    inserted_ids.append(str(instance.id))
                else:
                    inserted_ids.append(instance.id)

            # Fetch column names directly from the database
            table_name = model.__tablename__
            columns_query = text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = :table_name"
            )
            result = await session.execute(columns_query, {"table_name": table_name})
            columns = [row[0] for row in result]

            # Construct a query to select all columns for the inserted rows
            columns_str = ", ".join(columns)
            select_query = text(
                f"SELECT {columns_str} FROM {table_name} WHERE id = ANY(:ids)"
            )
            result = await session.execute(select_query, {"ids": inserted_ids})

            for row in result:
                row_dict = {}
                for column, value in zip(columns, row):
                    if isinstance(value, AsyncpgUUID):
                        value = str(value)
                    row_dict[column] = value
                inserted_rows.append(row_dict)

            await session.commit()
            log.info(f"Inserted {len(data)} rows into {model.__tablename__}")

        return inserted_ids, inserted_rows

    async def get_inference_result(
        self,
        model: Type[DeclarativeMeta],
        filters: dict[str, Any],
        batch_size: int = 6500,
    ) -> list[dict[str, Any]]:
        results = []
        offset = 0
        async with self.sessionmaker() as session:
            while True:
                query = select(model)
                filter_expression, params = _build_filter(model, filters)
                query = query.filter(filter_expression)

                query = query.limit(batch_size).offset(offset)
                batch_results = await session.execute(query, params)
                batch_results = batch_results.scalars().all()

                if not batch_results:
                    break

                results.extend(batch_results)
                offset += batch_size
                log.info(f"Fetching {results} from database")

        if not results:
            return []

        inference_results: list[dict[str, Any]] = []

        # Fetch column names directly from the database
        table_name = model.__tablename__
        columns_query = text(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = :table_name"
        )
        result = await session.execute(columns_query, {"table_name": table_name})
        columns = [row[0] for row in result]

        # Construct a query to select all columns for the inserted rows
        columns_str = ", ".join(columns)
        select_query = text(
            f"SELECT {columns_str} FROM {table_name} WHERE id = ANY(:ids)"
        )
        result = await session.execute(
            select_query, {"ids": [result.id for result in results]}
        )

        for row in result:
            row_dict = {}
            for column, value in zip(columns, row):
                if isinstance(value, AsyncpgUUID):
                    value = str(value)
                row_dict[column] = value
            inference_results.append(row_dict)

        return inference_results

    async def delete_inference_result(
        self,
        model: Type[DeclarativeMeta],
        filters: dict[str, Any],
    ) -> list[dict[Any, dict]]:
        deleted_rows: list[dict[str, Any]] = []

        async with self.sessionmaker() as session:
            filter_expression, params = _build_filter(model, filters)

            # Fetch column names
            table_name = model.__tablename__
            columns_query = text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = :table_name"
            )
            result = await session.execute(columns_query, {"table_name": table_name})
            columns = [row[0] for row in result]

            # Construct the SELECT query
            columns_str = ", ".join(columns)
            select_query = f"SELECT {columns_str} FROM {table_name}"

            # Convert the SQLAlchemy filter expression to a string
            where_clause = str(filter_expression)

            # Combine SELECT query with WHERE clause
            full_query = f"{select_query} WHERE {where_clause}"

            # Create a SQLAlchemy text object
            stmt = text(full_query)

            # Execute the query with params
            result = await session.execute(stmt, params)

            for row in result:
                row_dict = {}
                for column, value in zip(columns, row):
                    if isinstance(value, AsyncpgUUID):
                        value = str(value)
                    row_dict[column] = value
                deleted_rows.append(row_dict)

            # Perform the deletion
            delete_stmt = delete(model).where(filter_expression)
            await session.execute(delete_stmt, params)
            await session.commit()

        return deleted_rows

    async def update_inference_result(
        self,
        model: Type[DeclarativeMeta],
        filters: dict[str, Any],
        updated_data: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
        """Updates entries in the specified table based on the filters provided.

        Args:
            model (Type[DeclarativeMeta]): The SQLAlchemy model to update data of.
            filters (dict): The filters to apply to the query.
            updated_data (dict): The updates to apply to the target rows.
            is_and (bool, optional): Whether to treat the filters as an OR/AND condition. Defaults to True.

        Returns:
            tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
            A tuple containing:
            1. The updated rows
            2. The data necessary to reverse the update
        """

        updated_results: list[dict[str, Any]] = []
        original_results: list[dict[str, Any]] = []
        reverse_filters: dict[str, str] = {"boolean_clause": "OR", "conditions": []}

        async with self.sessionmaker() as session:
            filter_expression, params = _build_filter(model, filters)

            # Fetch column names
            table_name = model.__tablename__
            columns_query = text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = :table_name"
            )
            result = await session.execute(columns_query, {"table_name": table_name})
            columns = [row[0] for row in result]

            # Construct the SELECT query
            columns_str = ", ".join(columns)
            select_query = f"SELECT {columns_str} FROM {table_name}"

            # Convert the SQLAlchemy filter expression to a string
            where_clause = str(filter_expression)

            # Combine SELECT query with WHERE clause
            full_query = f"{select_query} WHERE {where_clause}"

            # Create a SQLAlchemy text object
            select_stmt = text(full_query)

            # Execute the query with params
            result = await session.execute(select_stmt, params)

            for row in result:
                row_dict = {}
                for column, value in zip(columns, row):
                    if isinstance(value, AsyncpgUUID):
                        value = str(value)
                    row_dict[column] = value
                original_results.append(row_dict)
                reverse_filters["conditions"].append(
                    {"column": "id", "operator": "=", "value": row_dict["id"]}
                )

            # Perform the update
            update_stmt = update(model).where(filter_expression).values(**updated_data)
            await session.execute(update_stmt, params)
            await session.commit()

            # Fetch the updated rows
            updated_filter_expression, updated_params = _build_filter(
                model, reverse_filters
            )
            updated_where_clause = str(updated_filter_expression)
            updated_full_query = f"{select_query} WHERE {updated_where_clause}"
            updated_select_stmt = text(updated_full_query)
            result = await session.execute(updated_select_stmt, updated_params)

            # Convert the updated rows to dictionaries
            for row in result:
                row_dict = {}
                for column, value in zip(columns, row):
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    if isinstance(value, AsyncpgUUID):
                        value = str(value)
                    row_dict[column] = value
                updated_results.append(row_dict)

            log.info(f"Updated {len(updated_results)} rows in database")

        # Create reverse updated_data
        reverse_updated_data = {}
        updated_sample = updated_results[0]
        original_sample = original_results[0]

        for key, value in updated_sample.items():
            if key == "updated_at":
                continue
            if original_sample[key] != value:
                reverse_updated_data[key] = original_sample[key]
        return updated_results, reverse_filters, reverse_updated_data

    async def static_get(
        self,
        orm_model: Type[DeclarativeMeta],
        pydantic_model: Type[BaseModel],
        filters: dict[str, Any],
        batch_size: int = 6500,
    ) -> list[BaseObject]:
        """Fetches entries from the specified table based on the filters provided.

        Args:
            orm_model (Type[DeclarativeMeta]): The SQLAlchemy ORM model to fetch data of.
            pydantic_model (Type[BaseModel]): The pydantic model to validate the ORM model to.
            filters (list[dict): The filters to apply to the query.

        Returns:
            list[BaseObject]: A list of BaseObject that match the filters.
        """
        results = []
        offset = 0
        async with self.sessionmaker() as session:
            while True:
                query = select(orm_model)
                filter_expression, params = _build_filter(orm_model, filters)
                query = query.filter(filter_expression)

                query = query.limit(batch_size).offset(offset)
                batch_results = await session.execute(query, params)
                batch_results = batch_results.scalars().all()

                if not batch_results:
                    break

                results.extend(batch_results)
                offset += batch_size
                log.info(f"Fetching {results} from database")

        if not results:
            return []
        return [pydantic_model.model_validate(result.__dict__) for result in results]

    async def static_post(
        self, orm_model: Type[DeclarativeMeta], data: list[dict[str, Any]]
    ) -> list[BaseObject]:
        """Inserts entries into the specified table.

        Args:
            orm_model (Type[DeclarativeMeta]): The SQLAlchemy ORM model to insert data into.
            data (list[dict[str, Any]]): The data to insert.

        Returns:
            list[BaseObject]: A list of BaseObject that were inserted.
        """
        orm_instances = [orm_model(**item) for item in data]
        async with self.sessionmaker() as session:
            session.add_all(orm_instances)
            await session.flush()
            await session.commit()
            log.info(f"Inserted {len(data)} rows into {orm_model.__tablename__}")

    async def static_update(
        self,
        orm_model: Type[DeclarativeMeta],
        filters: dict[str, Any],
        updated_data: Optional[dict[str, Any]],
        increment_field: Optional[str],
    ):
        """Updates entries in the specified table based on the filters provided.

        Args:
            orm_model (Type[DeclarativeMeta]): The SQLAlchemy model to update data of.
            filters (dict): The filters to apply to the query.
            updated_data (dict): The updates to apply to the target rows.
        """
        async with self.sessionmaker() as session:
            filter_expression, params = _build_filter(orm_model, filters)

            if increment_field:
                update_stmt = (
                    update(orm_model)
                    .where(filter_expression)
                    .values({increment_field: column(increment_field) + 1})
                )
            else:
                update_stmt = (
                    update(orm_model).where(filter_expression).values(**updated_data)
                )

            await session.execute(update_stmt, params)
            await session.commit()
            log.info(f"Updated rows in {orm_model.__tablename__}")

    ### Miscellaneous ###
    def get_column(
        self,
        model: Type[DeclarativeMeta],
        column: str,
        filters: dict,
        is_and: bool = True,
        batch_size: int = 6500,
    ) -> list[Any]:
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


def _build_filter(
    model: Type[DeclarativeMeta], filter_dict: dict[str, Any], param_prefix: str = "p"
) -> tuple[BinaryExpression, dict]:
    """Recursively builds a SQLAlchemy filter expression from the provided filter dictionary."""
    if not filter_dict:
        return true(), {}

    if "boolean_clause" in filter_dict:
        conditions = []
        params = {}
        for idx, condition in enumerate(filter_dict["conditions"]):
            sub_condition, sub_params = _build_filter(
                model, condition, f"{param_prefix}_{idx}"
            )
            conditions.append(sub_condition)
            params.update(sub_params)

        if len(conditions) == 0:
            return true(), {}
        elif len(conditions) == 1:
            return conditions[0], params
        else:
            return (
                and_(*conditions)
                if filter_dict["boolean_clause"] == "AND"
                else or_(*conditions)
            ), params

    elif (
        "column" in filter_dict and "operator" in filter_dict and "value" in filter_dict
    ):
        column = filter_dict["column"]
        value = filter_dict["value"]
        param_name = f"{param_prefix}"
        param_dict = {param_name: value}

        operators = {
            "=": "{} = :{}",
            "!=": "{} != :{}",
            ">": "{} > :{}",
            "<": "{} < :{}",
            ">=": "{} >= :{}",
            "<=": "{} <= :{}",
            "LIKE": "{} LIKE :{}",
            "IN": "{} IN (:{})" if isinstance(value, (list, tuple)) else "{} IN (:{})",
            "IS NOT": "{} IS NOT NULL" if value is None else "{} != :{}",
        }

        if filter_dict["operator"] in operators:
            if filter_dict["operator"] == "IN" and isinstance(value, (list, tuple)):
                in_params = {f"{param_name}_{i}": v for i, v in enumerate(value)}
                in_clause = ", ".join(f":{param_name}_{i}" for i in range(len(value)))
                return text(f"{column} IN ({in_clause})"), in_params
            else:
                return (
                    text(operators[filter_dict["operator"]].format(column, param_name)),
                    param_dict,
                )
        else:
            raise ValueError(f"Unsupported operator: {filter_dict['operator']}")

    else:
        raise ValueError(f"Invalid filter structure: {filter_dict}")
