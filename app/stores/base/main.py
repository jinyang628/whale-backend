# Use this script to do testing/one time operations on the database

import logging

from app.stores.base.object import ObjectStore

log = logging.getLogger(__name__)


def main():
    sql = """
    DROP TABLE IF EXISTS entry;
    """
    obj_store = ObjectStore(table_name="entry")
    obj_store.execute(
        sql=sql
    )


if __name__ == "__main__":
    main()
