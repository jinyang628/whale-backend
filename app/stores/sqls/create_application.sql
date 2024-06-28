DROP TABLE IF EXISTS application;

DROP TRIGGER IF EXISTS application_update_timestamp;

DROP TRIGGER IF EXISTS application_insert;

DROP TRIGGER IF EXISTS application_update;

DROP TRIGGER IF EXISTS application_delete;

CREATE TABLE application (
    id TEXT PRIMARY KEY,
    version INTEGER NOT NULL,
    name TEXT NOT NULL,
    tables TEXT NOT NULL,  
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(id),
    CHECK(version <> ''),
    CHECK(tables <> '')
)

CREATE TRIGGER application_insert
AFTER
INSERT
    ON application FOR EACH ROW BEGIN
VALUES
    (
        'application',
        NEW.id,
        json_object(
            'version', NEW.version,
            'name', NEW.name,
            'tables', NEW.tables
        ),
        'INSERT'
    );

END;

--- Trigger on Application Update
CREATE TRIGGER application_update
AFTER
UPDATE
    ON application FOR EACH ROW BEGIN
VALUES
    (
        'application',
        NEW.id,
        json_object(
            'version', NEW.version,
            'name', NEW.name,
            'tables', NEW.tables
        ),
        'UPDATE'
    );

UPDATE
    application
SET
    updated_at = CURRENT_TIMESTAMP
WHERE
    id = OLD.id;

END;

--- Trigger on Application Delete
CREATE TRIGGER application_delete
AFTER
    DELETE ON application FOR EACH ROW 
    BEGIN
VALUES
    (
        'application',
        OLD.id,
        json_object(
            'version', OLD.version,
            'name', OLD.name,
            'tables', OLD.tables
        ),
        'DELETE'
    );

END;