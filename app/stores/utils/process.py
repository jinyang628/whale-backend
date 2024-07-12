from datetime import date
from typing import Any
from dateutil import parser

from app.models.application import DataType, Table


def process_rows_to_insert(
    table: Table,
    rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    datetime_column_names_to_process: list[str] = []
    date_column_names_to_process: list[str] = []
    for column in table.columns:
        if column.data_type == DataType.DATETIME:
            datetime_column_names_to_process.append(column.name)
        if column.data_type == DataType.DATE:
            date_column_names_to_process.append(column.name)
    
    rows = _process_datetime_values(rows=rows, column_names_to_process=datetime_column_names_to_process)
    rows = _process_date_values(rows=rows, column_names_to_process=date_column_names_to_process)
    return rows
    

def _process_datetime_values(
    rows: list[dict[str, Any]], 
    column_names_to_process: list[str]
) -> list[dict[str, Any]]:
    modified_rows: list[dict[str, Any]] = []
    
    for row in rows:
        for column_name in column_names_to_process:
            if not row[column_name]:
                continue
            row[column_name] = parser.parse(row[column_name])
        modified_rows.append(row)
        
    return modified_rows

def _process_date_values(rows: list[dict[str, Any]], column_names_to_process: list[str]) -> list[dict[str, Any]]:
    modified_rows: list[dict[str, Any]] = []
    
    for row in rows:
        for column_name in column_names_to_process:
            if not row[column_name]:
                continue
            row[column_name] = parser.parse(row[column_name]).date()
        modified_rows.append(row)
        
    return modified_rows