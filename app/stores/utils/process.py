from datetime import date
import datetime
from typing import Any
from dateutil import parser

from app.models.application import DataType, Table


def process_rows_to_insert(
    table: Table,
    rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    datetime_column_names_to_process, date_column_names_to_process = _identify_columns_to_process(
        table=table
    )
    
    rows = _process_datetime_values_of_row(rows=rows, column_names_to_process=datetime_column_names_to_process)
    rows = _process_date_values_of_row(rows=rows, column_names_to_process=date_column_names_to_process)
    return rows
    
def process_filter_dict(
    table: Table,
    filter_dict: dict[str, Any]
) -> tuple[dict[str, Any], list[str], list[str]]:
    datetime_column_names_to_process, date_column_names_to_process = _identify_columns_to_process(
        table=table
    )
    
    filter_dict = _process_datetime_values_of_dict(filter_dict=filter_dict, column_names_to_process=datetime_column_names_to_process)
    filter_dict = _process_date_values_of_dict(filter_dict=filter_dict, column_names_to_process=date_column_names_to_process)
    
    return filter_dict, datetime_column_names_to_process, date_column_names_to_process
    
def _identify_columns_to_process(table: Table):
    datetime_column_names_to_process: list[str] = []
    date_column_names_to_process: list[str] = []
    for column in table.columns:
        if column.data_type == DataType.DATETIME:
            datetime_column_names_to_process.append(column.name)
        if column.data_type == DataType.DATE:
            date_column_names_to_process.append(column.name)
            
    return datetime_column_names_to_process, date_column_names_to_process

def _process_datetime_values_of_row(
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

def _process_date_values_of_row(rows: list[dict[str, Any]], column_names_to_process: list[str]) -> list[dict[str, Any]]:
    modified_rows: list[dict[str, Any]] = []
    
    for row in rows:
        for column_name in column_names_to_process:
            if not row[column_name]:
                continue
            row[column_name] = parser.parse(row[column_name]).date()
        modified_rows.append(row)
        
    return modified_rows

def _process_datetime_values_of_dict(
    filter_dict: dict[str, Any], 
    column_names_to_process: list[str]
) -> dict[str, Any]:
    for column_name in column_names_to_process:
        if column_name not in filter_dict:
            continue 
        if not filter_dict[column_name]:
            continue 
        filter_dict[column_name] = parser.parse(filter_dict[column_name])
        
    return filter_dict

def _process_date_values_of_dict(
    filter_dict: dict[str, Any], 
    column_names_to_process: list[str]
) -> dict[str, Any]:
    for column_name in column_names_to_process:
        if column_name not in filter_dict:
            continue 
        if not filter_dict[column_name]:
            continue 
        filter_dict[column_name] = parser.parse(filter_dict[column_name]).date()
        
    return filter_dict

def process_rows_to_return(
    rows: list[dict[str, Any]],
    datetime_column_names_to_process: list[str],
    date_column_names_to_process: list[str]
) -> list[dict[str, Any]]:
    for name in datetime_column_names_to_process + date_column_names_to_process:
        for row in rows:
            if value := row.get(name):
                if isinstance(value, (date, datetime)):
                    row[name] = value.isoformat()
    return rows
                
