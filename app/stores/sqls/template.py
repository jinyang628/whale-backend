from app.models.application import Column, DataType

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
    json_object_pairs = []
    for col in columns:
        sql_type = get_sql_type(col.data_type)
        nullable = "" if col.nullable else " NOT NULL"
        column_defs.append(f"    {col.name} {sql_type}{nullable}")
        json_object_pairs.append(f"'{col.name}', NEW.{col.name}")

    column_defs_str = ",\n".join(column_defs)
    json_object_str = ", ".join(json_object_pairs)
    
    script = f"""
DROP TABLE IF EXISTS {table_name};
##
DROP TRIGGER IF EXISTS {table_name}_update_timestamp ON {table_name};
##
DROP TRIGGER IF EXISTS {table_name}_insert ON {table_name};
##
DROP TRIGGER IF EXISTS {table_name}_update ON {table_name};
##
DROP TRIGGER IF EXISTS {table_name}_delete ON {table_name};
##
CREATE TABLE {table_name} (
    {column_defs_str},
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(id)
);
##
CREATE OR REPLACE FUNCTION {table_name}_insert_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO changes (table_name, record_id, data, operation)
    VALUES (
        '{table_name}',
        NEW.id,
        json_build_object({json_object_str}),
        'INSERT'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
##
CREATE TRIGGER {table_name}_insert
AFTER INSERT ON {table_name}
FOR EACH ROW EXECUTE FUNCTION {table_name}_insert_trigger();
##
CREATE OR REPLACE FUNCTION {table_name}_update_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO changes (table_name, record_id, data, operation)
    VALUES (
        '{table_name}',
        NEW.id,
        json_build_object({json_object_str}),
        'UPDATE'
    );
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
##
CREATE TRIGGER {table_name}_update
BEFORE UPDATE ON {table_name}
FOR EACH ROW EXECUTE FUNCTION {table_name}_update_trigger();
##
CREATE OR REPLACE FUNCTION {table_name}_delete_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO changes (table_name, record_id, data, operation)
    VALUES (
        '{table_name}',
        OLD.id,
        json_build_object({json_object_str.replace('NEW.', 'OLD.')}),
        'DELETE'
    );
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
##
CREATE TRIGGER {table_name}_delete
AFTER DELETE ON {table_name}
FOR EACH ROW EXECUTE FUNCTION {table_name}_delete_trigger();
"""
    print(script)
    return script