def generate_sql_script(table_name):
    script = f"""
DROP TABLE IF EXISTS {table_name};
##
DROP TRIGGER IF EXISTS {table_name}_update_timestamp;
##
DROP TRIGGER IF EXISTS {table_name}_insert;
##
DROP TRIGGER IF EXISTS {table_name}_update;
##
DROP TRIGGER IF EXISTS {table_name}_delete;
##
CREATE TABLE {table_name} (
    id TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    name TEXT NOT NULL,
    tables TEXT NOT NULL,  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(id),
    UNIQUE(name),
    CHECK(version <> ''),
    CHECK(tables <> '')
)
##
CREATE TRIGGER {table_name}_insert
AFTER
INSERT
    ON {table_name} FOR EACH ROW BEGIN
VALUES
    (
        '{table_name}',
        NEW.id,
        json_object(
            'version', NEW.version,
            'name', NEW.name,
            'tables', NEW.tables
        ),
        'INSERT'
    );

END;
##
CREATE TRIGGER {table_name}_update
AFTER
UPDATE
    ON {table_name} FOR EACH ROW BEGIN
VALUES
    (
        '{table_name}',
        NEW.id,
        json_object(
            'version', NEW.version,
            'name', NEW.name,
            'tables', NEW.tables
        ),
        'UPDATE'
    );

UPDATE
    {table_name}
SET
    updated_at = CURRENT_TIMESTAMP
WHERE
    id = OLD.id;

END;
##
CREATE TRIGGER {table_name}_delete
AFTER
    DELETE ON {table_name} FOR EACH ROW 
    BEGIN
VALUES
    (
        '{table_name}',
        OLD.id,
        json_object(
            'version', OLD.version,
            'name', OLD.name,
            'tables', OLD.tables
        ),
        'DELETE'
    );

END;
"""
    return script