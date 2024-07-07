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
    }
    return sql_type_map[data_type]

# TODO: Implement some sort of versioning system so clients can update their tables without breaking the application/dropping the entire table
# TODO: Implement unique constraints that can be controlled by clients when creating applications
def generate_sql_script(table_name: str, columns: list[Column]):
    # Generate column definitions
    column_defs = []
    for col in columns:
        sql_type = get_sql_type(col.data_type)
        nullable = "" if col.nullable else " NOT NULL"
        default = f" DEFAULT {col.default_value}" if col.default_value is not None else ""

        
        if col.primary_key != PrimaryKey.NONE:
            match col.primary_key:
                case PrimaryKey.AUTO_INCREMENT:
                    sql_type = "INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
                # TODO: Implement UUID condition
                # case PrimaryKey.UUID:
                #     sql_type = "UUID PRIMARY KEY DEFAULT gen_random_uuid()"
                case _:
                    raise ValueError(f"Unsupported primary key type: {col.primary_key}")
                
        column_defs.append(f"    {col.name} {sql_type}{nullable}")

    column_defs_str = ",\n".join(column_defs)
    
    script = f"""
DROP TABLE IF EXISTS {table_name};
##
DROP TRIGGER IF EXISTS {table_name}_update_timestamp ON {table_name};
##
DROP TRIGGER IF EXISTS {table_name}_update ON {table_name};
##
CREATE TABLE {table_name} (
    {column_defs_str},
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
##
CREATE OR REPLACE FUNCTION {table_name}_update_trigger()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
##
CREATE TRIGGER {table_name}_update
BEFORE UPDATE ON {table_name}
FOR EACH ROW EXECUTE FUNCTION {table_name}_update_trigger();
"""
    log.info(script)
    return script