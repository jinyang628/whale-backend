from typing import Any
import uuid

from dateutil import parser

from app.models.application.base import DataType, Table


def process_client_facing_rows(
    db_rows: list[dict[str, Any]],
    datetime_column_names_to_process: list[str],
    date_column_names_to_process: list[str],
    uuid_column_names_to_process: list[str],
) -> list[dict[str, Any]]:
    for name in datetime_column_names_to_process + date_column_names_to_process:
        for row in db_rows:
            if value := row.get(name):
                if not value:
                    continue
                row[name] = value.isoformat()
    for name in uuid_column_names_to_process:
        for row in db_rows:
            if value := row.get(name):
                if not value:
                    continue
                row[name] = str(value)
    return db_rows


def process_client_facing_update_dict(
    db_dict: dict[str, Any],
    datetime_column_names_to_process: list[str],
    date_column_names_to_process: list[str],
    uuid_column_names_to_process: list[str],
) -> dict[str, Any]:
    for name in datetime_column_names_to_process + date_column_names_to_process:
        if name in db_dict and db_dict[name]:
            db_dict[name] = db_dict[name].isoformat()
            
    for name in uuid_column_names_to_process:
        if name in db_dict and db_dict[name]:
            db_dict[name] = str(db_dict[name])
            
    return db_dict


def process_client_facing_filter_dict(
    db_dict: dict[str, Any],
    datetime_column_names_to_process: list[str],
    date_column_names_to_process: list[str],
    uuid_column_names_to_process: list[str],
) -> dict[str, Any]:
    def process_conditions_helper(
        conditions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        for condition in conditions:
            if "boolean_clause" in condition:
                condition["conditions"] = process_conditions_helper(
                    condition["conditions"]
                )
            else:
                if (
                    ("column" not in condition)
                    or ("operator" not in condition)
                    or ("value" not in condition)
                ):
                    raise ValueError("Invalid condition structure")
                if not condition["value"]:
                    continue
                if condition["column"] in datetime_column_names_to_process:
                    condition["value"] = condition["value"].isoformat()
                if condition["column"] in date_column_names_to_process:
                    condition["value"] = condition["value"].isoformat()
                if condition["column"] in uuid_column_names_to_process:
                    condition["value"] = str(condition["value"])

        return conditions

    if "conditions" in db_dict:
        db_dict["conditions"] = process_conditions_helper(db_dict["conditions"])
    return db_dict


def identify_columns_to_process(table: Table):
    """Date, datetime, and uuid are not serialisable to JSON (which is important for the request body of API calls). This function identifies these columns so that subsequent logic can process them before returning the API response."""
    datetime_column_names_to_process: list[str] = []
    date_column_names_to_process: list[str] = []
    uuid_column_names_to_process: list[str] = []
    
    for column in table.columns:
        if column.data_type == DataType.DATETIME:
            datetime_column_names_to_process.append(column.name)
        if column.data_type == DataType.DATE:
            date_column_names_to_process.append(column.name)
        if column.data_type == DataType.UUID:
            uuid_column_names_to_process.append(column.name)
            
    if table.primary_key == DataType.UUID:
        uuid_column_names_to_process.append("id")

    datetime_column_names_to_process.extend(["created_at", "updated_at"])
    return datetime_column_names_to_process, date_column_names_to_process, uuid_column_names_to_process


def process_values_of_row(
    rows: list[dict[str, Any]],
    datetime_column_names_to_process: list[str],
    date_column_names_to_process: list[str],
    uuid_column_names_to_process: list[str],
) -> list[dict[str, Any]]:
    modified_rows: list[dict[str, Any]] = []

    for row in rows:
        for column_name in datetime_column_names_to_process:
            if not row.get(column_name):
                continue
            row[column_name] = parser.parse(row[column_name])

        for column_name in date_column_names_to_process:
            if not row.get(column_name):
                continue
            row[column_name] = parser.parse(row[column_name]).date()
            
        for column_name in uuid_column_names_to_process:
            if not row.get(column_name):
                continue
            row[column_name] = str(row[column_name])
        modified_rows.append(row)

    return modified_rows


def process_datetime_or_date_values_of_filter_dict(
    dict_to_process: dict[str, Any],
    datetime_column_names_to_process: list[str],
    date_column_names_to_process: list[str],
    uuid_column_names_to_process: list[str],
) -> dict[str, Any]:

    def process_conditions_helper(
        conditions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        for condition in conditions:
            if "boolean_clause" in condition:
                condition["conditions"] = process_conditions_helper(
                    condition["conditions"]
                )
            else:
                if (
                    ("column" not in condition)
                    or ("operator" not in condition)
                    or ("value" not in condition)
                ):
                    raise ValueError("Invalid condition structure")
                if not condition["value"]:
                    continue
                if condition["column"] in datetime_column_names_to_process:
                    condition["value"] = parser.parse(condition["value"])
                if condition["column"] in date_column_names_to_process:
                    condition["value"] = parser.parse(condition["value"]).date()
                if condition["column"] in uuid_column_names_to_process:
                    condition["value"] = uuid.UUID(condition["value"])

        return conditions

    if "conditions" in dict_to_process:
        dict_to_process["conditions"] = process_conditions_helper(
            dict_to_process["conditions"]
        )
    return dict_to_process


def process_datetime_or_date_values_of_update_dict(
    dict_to_process: dict[str, Any],
    datetime_column_names_to_process: list[str],
    date_column_names_to_process: list[str],
    uuid_column_names_to_process: list[str],
) -> dict[str, Any]:
    for key, value in dict_to_process.items():
        if not value:
            continue

        if key in datetime_column_names_to_process:
            dict_to_process[key] = parser.parse(value)
        if key in date_column_names_to_process:
            dict_to_process[key] = parser.parse(value).date()
        if key in uuid_column_names_to_process:
            dict_to_process[key] = uuid.UUID(value)

    return dict_to_process


# Input shape of filter dict
"""
    {
        "boolean_clause": "AND",
        "conditions": [
            { 
                "column": "rating", 
                "operator": "=", 
                "value": 1 
            },
            {
            "boolean_clause": "OR",
            "conditions": [
                {
                    "column": "application_name",
                    "operator": "=",
                    "value": "task_tracker"
                },
                { 
                    "column": "user_id", 
                    "operator": "=", 
                    "value": "Jin Yang" 
                }
            ]
            }
        ]
    }
"""
