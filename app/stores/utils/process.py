from datetime import date
import datetime
from typing import Any
from dateutil import parser

from app.models.application import DataType, Table


def process_db_facing_rows(
    table: Table,
    client_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    datetime_column_names_to_process, date_column_names_to_process = _identify_columns_to_process(
        table=table
    )
    
    client_rows = _process_datetime_values_of_row(rows=client_rows, column_names_to_process=datetime_column_names_to_process)
    client_rows = _process_date_values_of_row(rows=client_rows, column_names_to_process=date_column_names_to_process)
    return client_rows
    
def process_db_facing_dict(
    table: Table,
    client_dict: dict[str, Any]
) -> tuple[dict[str, Any], list[str], list[str]]:
    datetime_column_names_to_process, date_column_names_to_process = _identify_columns_to_process(
        table=table
    )
    
    client_dict = _process_datetime_values_of_dict(dict_to_process=client_dict, column_names_to_process=datetime_column_names_to_process)
    client_dict = _process_date_values_of_dict(dict_to_process=client_dict, column_names_to_process=date_column_names_to_process)
    
    return client_dict, datetime_column_names_to_process, date_column_names_to_process
    
def process_client_facing_rows(
    db_rows: list[dict[str, Any]],
    datetime_column_names_to_process: list[str],
    date_column_names_to_process: list[str]
) -> list[dict[str, Any]]:
    for name in datetime_column_names_to_process + date_column_names_to_process:
        for row in db_rows:
            if value := row.get(name):
                if not value:
                    continue
                row[name] = value.isoformat()
    return db_rows
       
def process_client_facing_dict(
    db_dict: dict[str, Any],
    datetime_column_names_to_process: list[str],
    date_column_names_to_process: list[str]
) -> dict[str, Any]:
    for name in datetime_column_names_to_process + date_column_names_to_process:
        if name in db_dict and db_dict[name]:
            db_dict[name] = db_dict[name].isoformat()
    return db_dict
                

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
    dict_to_process: dict[str, Any], 
    column_names_to_process: list[str]
) -> dict[str, Any]:
    for column_name in column_names_to_process:
        if column_name not in dict_to_process:
            continue 
        if not dict_to_process[column_name]:
            continue 
        dict_to_process[column_name] = parser.parse(dict_to_process[column_name])
        
    return dict_to_process

def _process_date_values_of_dict(
    dict_to_process: dict[str, Any], 
    column_names_to_process: list[str]
) -> dict[str, Any]:
    for column_name in column_names_to_process:
        if column_name not in dict_to_process:
            continue 
        if not dict_to_process[column_name]:
            continue 
        dict_to_process[column_name] = parser.parse(dict_to_process[column_name]).date()
        
    return dict_to_process


