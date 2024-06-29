import logging
from app.models.application import Column

from app.stores.base.object import ObjectStore
from app.stores.sqls.template import generate_sql_script

log = logging.getLogger(__name__)

def generate_client_table(table_name: str, columns: list[Column], db_url: str, db_auth_token: str):
    obj_store = ObjectStore(table_name=table_name, url=db_url, auth_token=db_auth_token)
    sql_script = generate_sql_script(table_name=table_name, columns=columns)
    sql_statements = sql_script.split("##")    
    for statement in sql_statements:
        if statement.strip():
            obj_store.execute(sql=statement)
