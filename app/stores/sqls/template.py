from datetime import date
import datetime
from app.models.application import Column, DataType, PrimaryKey
import logging

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# TODO: The mapping here is important because not every database has the same types. And it doesn't seem like a good idea that we update valid SDK data types everytime we change a DB? The mapping here represents what is valid for SQLite, which will change IF we ever change databases
def get_sql_type(data_type: DataType) -> str:
    sql_type_map = {
        DataType.STRING: "TEXT",
        DataType.INTEGER: "INTEGER",
        DataType.FLOAT: "REAL",
        DataType.BOOLEAN: "BOOLEAN",
        DataType.DATE: "DATE",
        DataType.DATETIME: "TIMESTAMPTZ",
        DataType.UUID: "UUID",
        DataType.ENUM: "ENUM",
    }
    return sql_type_map[data_type]


# TODO: Implement some sort of versioning system so clients can update their tables without breaking the application/dropping the entire table
# TODO: Implement unique constraints that can be controlled by clients when creating applications

def generate_table_creation_script(
    application_name: str,
    table_name: str, 
    columns: list[Column],
    primary_key: PrimaryKey,
    enable_created_at_timestamp: bool,
    enable_updated_at_timestamp: bool,
):
    """Generates SQL script for creating a table."""
    column_defs = []
    enum_types = []

    match primary_key:
        case PrimaryKey.AUTO_INCREMENT:
            column_defs.append("    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY")
        case PrimaryKey.UUID:
            column_defs.append("    id UUID PRIMARY KEY DEFAULT gen_random_uuid()")
        case _:
            raise ValueError(f"Unsupported primary key type: {primary_key}")

    for col in columns:
        sql_type = get_sql_type(col.data_type)
        nullable = "" if col.nullable else " NOT NULL"
        unique = " UNIQUE" if col.unique else ""

        if col.default_value is not None:
            if isinstance(col.default_value, str):
                default = f" DEFAULT '{col.default_value}'"
            elif isinstance(col.default_value, bool):
                default = f" DEFAULT {'TRUE' if col.default_value else 'FALSE'}"
            else:
                default = f" DEFAULT {col.default_value}"
        else:
            default = ""

        if sql_type.upper() == 'ENUM':
            enum_name = f"{table_name}_{col.name}_enum"
            enum_values = ", ".join(f"'{v}'" for v in col.enum_values)
            enum_types.append(f"DROP TYPE IF EXISTS {enum_name};") ## TODO: This will be problematic as different applications might drop each other's enum. We need to associate the application id to this
            enum_types.append(f"CREATE TYPE {enum_name} AS ENUM ({enum_values});")
            sql_type = enum_name

        column_defs.append(f"    {col.name} {sql_type}{nullable}{default}{unique}")

    if enable_created_at_timestamp:
        column_defs.append("    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP")

    if enable_updated_at_timestamp:
        column_defs.append("    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP")

    column_defs_str = ",\n".join(column_defs)

    script = f"DROP TABLE IF EXISTS {table_name} CASCADE; ##\n"

    for enum_type in enum_types:
        script += f"{enum_type}\n##"

    if enable_updated_at_timestamp:
        script += """
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql; ##
"""

    script += f"""
CREATE TABLE {table_name} (
{column_defs_str}
); ##
"""

    if enable_updated_at_timestamp:
        script += f"""
CREATE TRIGGER update_{table_name}_updated_at
BEFORE UPDATE ON {table_name}
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
##
"""

    return script


def generate_foreign_key_script(
    table_name: str, columns: list[Column], input_name: str
):
    """Generates SQL script for adding foreign key constraints to a table."""
    foreign_key_statements = []
    for col in columns:
        if col.foreign_key:
            fk_script = f"""
ALTER TABLE {table_name}
ADD CONSTRAINT fk_{table_name}_{col.name}
FOREIGN KEY ({col.name}) REFERENCES {input_name}_{col.foreign_key.table}({col.foreign_key.column});
##"""
            foreign_key_statements.append(fk_script)

    return "".join(foreign_key_statements)
