# Use this script to do testing/one time operations on the database

import logging

from app.stores.base.object import ObjectStore
from app.stores.sqls.template import generate_sql_script

log = logging.getLogger(__name__)


def main(table_name):
    obj_store = ObjectStore(table_name=table_name)
    sql_script = generate_sql_script(table_name=table_name)
    sql_statements = sql_script.split("##")
    
    for statement in sql_statements:
        # Skip empty statements
        if statement.strip():
            obj_store.execute(sql=statement)

if __name__ == "__main__":
    main(table_name="test")
