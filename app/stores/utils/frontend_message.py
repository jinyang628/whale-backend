from typing import Any, Union

def translate_filter_dict(filter_dict: Union[dict[str, Any], list[dict[str, Any]]]) -> str:
    def process_condition(condition: dict[str, Any]) -> str:
        if "boolean_clause" in condition:
            return translate_filter_dict(condition)
        return f"{condition['column']} {condition['operator']} {condition['value']}"

    if isinstance(filter_dict, list):
        return f" {filter_dict['boolean_clause']} ".join(process_condition(condition) for condition in filter_dict)

    if "boolean_clause" not in filter_dict:
        return process_condition(filter_dict)

    boolean_clause = filter_dict["boolean_clause"]
    conditions = filter_dict["conditions"]
    
    processed_conditions = [process_condition(condition) for condition in conditions]
    
    if len(processed_conditions) == 1:
        return processed_conditions[0]
    
    joined_conditions = f" {boolean_clause} ".join(processed_conditions)
    return f"({joined_conditions})" if len(conditions) > 1 else joined_conditions