import logging
import os
from datetime import datetime
from typing import Any, List

import libsql_client
from pydantic import BaseModel

from app.connectors.turso import TursoConnector


class ObjectStore:
    _table_name: str = None
    _db_client: TursoConnector = None

    def __init__(
        self,
        table_name: str,
        url: str,
        auth_token: str,
    ):
        self._table_name = table_name
        self._db_client = TursoConnector(
            url=url,
            auth_token=auth_token,
        )

    ####
    #### TABLE OPERATIONS
    ####

    def create_table(
        self,
        table_name: str,
        columns: dict,
    ) -> None:
        column_defs = []
        for column_name, column_type in columns.items():
            column_defs.append(f"{column_name} {column_type}")

        sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
        try:
            statement = libsql_client.Statement(sql=sql)
            self._db_client.execute(statement=statement)
            logging.info(f"Table {table_name} created successfully.")
        except Exception as e:
            logging.error(f"Error creating table {table_name}: {e}")
            raise e

    def delete_table(
        self,
        table_name: str,
    ) -> None:
        sql = f"DROP TABLE IF EXISTS {table_name}"
        try:
            statement = libsql_client.Statement(sql=sql)
            self._db_client.execute(statement=statement)
            logging.info(f"Table {table_name} deleted successfully.")
        except Exception as e:
            logging.error(f"Error deleting table {table_name}: {e}")
            raise e

    def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
    ) -> None:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        try:
            statement = libsql_client.Statement(sql=sql)
            self._db_client.execute(statement=statement)
            logging.info(
                f"Column {column_name} added to table {table_name} successfully."
            )
        except Exception as e:
            logging.error(
                f"Error adding column {column_name} to table {table_name}: {e}"
            )
            raise e

    ####
    #### CRUD
    ####

    def get(
        self,
        ids: List[str],
    ) -> List[dict]:
        statement = self._ids_to_get_statement(table_name=self._table_name, ids=ids)
        try:
            rs = self._db_client.execute(statement=statement)
            logging.debug(rs.rows)
            _dicts = [
                {rs.columns[i]: row[i] for i in range(len(rs.columns))}
                for row in rs.rows
            ]
            return _dicts
        except Exception as e:
            logging.error(f"Error found for statement {statement.sql}: {e}")
            raise e

    def delete(
        self,
        ids: List[str],
    ) -> bool:
        statement = self._ids_to_delete_statement(table_name=self._table_name, ids=ids)
        try:
            rs = self._db_client.execute(statement=statement)
            logging.debug(rs.rows_affected)
            return rs.rows_affected == len(ids)
        except Exception as e:
            logging.error(f"Error found for statement {statement.sql}: {e}")
            raise e

    def insert(
        self,
        objs: List[dict],
        return_column: str,
    ) -> List[any]:
        statements = [
            self._dict_to_insert_statement(table_name=self._table_name, dict=obj)
            for obj in objs
        ]

        try:
            rss = self._db_client.batch_execute(statements=statements)
            rowids = [r.last_insert_rowid for r in rss]
            logging.debug(rowids)
            _dicts = self._get_by_rowids(rowids=rowids)
            return [d[return_column] for d in _dicts]
        except Exception as e:
            logging.error(f"Error raised for SQL {[st.sql for st in statements]}: {e}")
            raise e

    def update(
        self,
        objs: List[dict],
    ) -> bool:
        statements = [
            self._dict_to_update_statement(table_name=self._table_name, dict=obj)
            for obj in objs
        ]
        try:
            rss = self._db_client.batch_execute(statements=statements)
            total_affected = sum([rs.rows_affected for rs in rss])
            logging.debug(total_affected)
            return total_affected == len(objs)
        except Exception as e:
            logging.error(f"Error raised for SQL {[st.sql for st in statements]}: {e}")
            raise e

    def execute(
        self,
        sql: str,
    ) -> List[dict]:
        statement = libsql_client.Statement(sql=sql)
        try:
            rs = self._db_client.execute(statement=statement)
            logging.debug(rs.rows)
            _dicts = [
                {rs.columns[i]: row[i] for i in range(len(rs.columns))}
                for row in rs.rows
            ]
            return _dicts
        except Exception as e:
            logging.error(f"Error found for statement {statement.sql}: {e}")
            raise e

    def _get_by_rowids(
        self,
        rowids: List[int],
    ) -> List[dict]:
        sql = f"""SELECT *
                    FROM {self._table_name}
                    WHERE rowid IN ({','.join([self._value_to_sql_value(rowid) for rowid in rowids])})"""
        return self.execute(sql=sql)

    ####
    #### SQL Statements
    ####

    def _dict_to_insert_statement(
        self,
        table_name: str,
        dict: dict,
    ) -> libsql_client.Statement:
        _dict = {k: v for k, v in dict.items() if k not in ["created_at", "updated_at"]}

        # TODO: Right now, we are manually processing the string to be compatible with SQLite. This is not the best practice and we should integrate an ORM somehow.
        # Manually construct values string
        values = []
        for v in _dict.values():
            if isinstance(v, str):
                # Escape single quotes in strings
                escaped_value = v.replace("'", "''")
                value_str = f"'{escaped_value}'"
            elif v is None:
                value_str = "NULL"
            else:
                value_str = str(v)
            values.append(value_str)

        columns = ", ".join(_dict.keys())
        values_str = ", ".join(values)
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values_str})"

        logging.debug(sql)

        return libsql_client.Statement(sql=sql)

    def _dict_to_update_statement(
        self,
        table_name: str,
        dict: dict,
    ) -> libsql_client.Statement:
        _dict = dict.copy()
        _id = _dict.get("id")
        if "id" in _dict:
            _dict.pop("id")
        if "created_at" in _dict:
            _dict.pop("created_at")
        if "updated_at" in _dict:
            _dict.pop("updated_at")

        # _iter = _dict.copy()
        # for k, v in _iter.items():
        #     if v is None:
        #         _dict.pop(k)

        sql = f"""UPDATE {table_name}
                    SET {','.join([f'{k}={self._value_to_sql_value(v)}' for k, v in _dict.items()])}
                    WHERE id = {self._value_to_sql_value(_id)}"""
        logging.debug(sql)

        return libsql_client.Statement(sql=sql)

    def _ids_to_delete_statement(
        self,
        table_name: str,
        ids: List[str],
    ) -> libsql_client.Statement:
        sql = f"""DELETE 
                    FROM {table_name}
                    WHERE id IN ({','.join([self._value_to_sql_value(id) for id in ids])})"""
        logging.debug(sql)

        return libsql_client.Statement(sql=sql)

    def _specified_column_to_delete_statement(
        self,
        table_name: str,
        specified_column: str,
        values: List[str],
    ) -> libsql_client.Statement:
        sql = f"""DELETE 
                    FROM {table_name}
                    WHERE {specified_column} IN ({','.join([self._value_to_sql_value(value) for value in values])})"""
        logging.debug(sql)

        return libsql_client.Statement(sql=sql)

    def _ids_to_get_statement(
        self,
        table_name: str,
        ids: List[str],
    ) -> libsql_client.Statement:
        sql = f"""SELECT * 
                    FROM {table_name} 
                    WHERE id IN ({','.join([self._value_to_sql_value(id) for id in ids])})"""
        logging.debug(sql)
        return libsql_client.Statement(sql=sql)

    def _value_to_sql_value(
        self,
        value: any,
    ) -> str:
        if value is None:
            return f"NULL"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, int):
            return f"{value}"
        elif isinstance(value, datetime):
            return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
        elif isinstance(value, bool):
            return f"{value}"
        elif isinstance(value, float):
            return f"{value}"
        elif isinstance(value, List) and all(isinstance(e, str) for e in value):
            return f"'{','.join([str(v) for v in value])}'"
        elif isinstance(value, List) and all(isinstance(e, int) for e in value):
            return f"'{','.join([str(v) for v in value])}'"
        # elif isinstance(value, None):
        #     return f"NULL"
        else:
            raise Exception(f"Unknown type: {type(value)}")

    ####
    #### COMMON
    ####

    def get_rows_by_matching_condition(
        self, column_to_match: str, matching_value: Any
    ) -> List[Any]:
        """
        Get all rows where column_to_match equals matching_value.

        Args:
            column_to_match (str): The column to amtch against.
            matching_value (Any): The value to match in column_to_match.

        Returns:
            List[Any]: The desired list of rows/objects which the table stores
        """
        sql = f"""SELECT *
                    FROM {self._table_name}
                    WHERE {column_to_match} = {self._value_to_sql_value(matching_value)}"""
        logging.debug(sql)
        try:
            statement = libsql_client.Statement(sql=sql)
            rs = self._db_client.execute(statement=statement)
            return [row for row in rs.rows]
        except Exception as e:
            logging.error(f"Error found for statement {statement.sql}: {e}")
            raise e

    def get_values_by_matching_condition(
        self, column_to_match: str, matching_value: Any, column_to_return: str
    ) -> List[Any]:
        """
        Get values from column_to_return for rows where column_to_match equals matching_value.

        Args:
        column_to_match (str): The column to match against.
        matching_value (any): The value to match in column_to_match.
        column_to_return (str): The column from which to return values.

        Returns:
        List[any]: A list of values from column_to_return.
        """
        sql = f"""SELECT {column_to_return}
                  FROM {self._table_name}
                  WHERE {column_to_match} = {self._value_to_sql_value(matching_value)}"""
        logging.debug(sql)
        try:
            statement = libsql_client.Statement(sql=sql)
            rs = self._db_client.execute(statement=statement)
            return [row[0] for row in rs.rows]
        except Exception as e:
            logging.error(f"Error found for statement {statement.sql}: {e}")
            raise e

    def delete_with_specified_column(
        self,
        specified_column: str,
        values: List[str],
    ) -> bool:
        statement = self._specified_column_to_delete_statement(
            table_name=self._table_name,
            specified_column=specified_column,
            values=values,
        )
        try:
            rs = self._db_client.execute(statement=statement)
            logging.debug(rs.rows_affected)
            return rs.rows_affected == len(values)
        except Exception as e:
            logging.error(f"Error found for statement {statement.sql}: {e}")
            raise e

    ####
    #### CONVERSION
    ####

    def get_model_columns(self, model: BaseModel) -> list:
        """Extract column names from a Pydantic model."""
        return list(model.model_fields.keys())

    def convert_row_to_dict(self, row: Any, model: BaseModel) -> dict[str, Any]:
        """Convert a Row object to a dictionary using column names from the model."""
        columns = self.get_model_columns(model)
        return dict(zip(columns, row))
