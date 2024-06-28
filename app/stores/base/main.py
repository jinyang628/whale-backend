# Use this script to do testing/one time operations on the database

import logging

from app.stores.base.object import ObjectStore

log = logging.getLogger(__name__)


def main():
    sql = """
CREATE TRIGGER entry_delete
AFTER
    DELETE ON entry FOR EACH ROW 
    BEGIN
VALUES
    (
        'entry',
        OLD.id,
        json_object(
            'version', OLD.version,
            'name', OLD.name,
            'application', OLD.application
        ),
        'DELETE'
    );

END;
"""
    obj_store = ObjectStore(table_name="entry")
    obj_store.execute(
        sql=sql
    )


if __name__ == "__main__":
    main()
