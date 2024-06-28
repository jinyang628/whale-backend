# Use this script to do testing/one time operations on the database

import logging

from app.stores.base.object import ObjectStore

log = logging.getLogger(__name__)


def main():
    sql = """
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

END;"""
    obj_store = ObjectStore(table_name="application")
    obj_store.execute(
        sql=sql
    )


if __name__ == "__main__":
    main()
