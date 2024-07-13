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
    }
    return sql_type_map[data_type]


# TODO: Implement some sort of versioning system so clients can update their tables without breaking the application/dropping the entire table
# TODO: Implement unique constraints that can be controlled by clients when creating applications

def generate_table_creation_script(table_name: str, columns: list[Column]):
    """Generates SQL script for creating a table."""
    column_defs = []
    for col in columns:
        sql_type = get_sql_type(col.data_type)
        nullable = "" if col.nullable else " NOT NULL"
        unique = " UNIQUE" if col.unique else ""

        if col.primary_key != PrimaryKey.NONE:
            match col.primary_key:
                case PrimaryKey.AUTO_INCREMENT:
                    sql_type = "INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
                case PrimaryKey.UUID:
                    sql_type = "UUID PRIMARY KEY DEFAULT gen_random_uuid()"
                case _:
                    raise ValueError(f"Unsupported primary key type: {col.primary_key}")
            default = ""  # Do not set default for primary key
        else:
            if col.default_value is not None:
                if isinstance(col.default_value, str):
                    default = f" DEFAULT '{col.default_value}'"
                elif isinstance(col.default_value, bool):
                    default = f" DEFAULT {'TRUE' if col.default_value else 'FALSE'}"
                else:
                    default = f" DEFAULT {col.default_value}"
            else:
                default = ""

        column_defs.append(f"    {col.name} {sql_type}{nullable}{default}{unique}")

    column_defs_str = ",\n".join(column_defs)

    script = f"""
DROP TABLE IF EXISTS {table_name} CASCADE;
##
CREATE TABLE {table_name} (
{column_defs_str}
);
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
