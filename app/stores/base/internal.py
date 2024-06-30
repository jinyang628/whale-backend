from app.stores.base.object import ObjectStore
import json
import logging
import os
from typing import Optional, Tuple, Type
from sqlalchemy.orm.decl_api import DeclarativeMeta

from dotenv import find_dotenv, load_dotenv

from app.connectors.orm import Orm
from app.models.application import Table
from app.models.inference import ApplicationContent, HttpMethod, InferenceResponse
from app.models.message import PostMessageResponse
from app.models.stores.application import Application, ApplicationORM
from app.models.stores.dynamic import create_dynamic_orm

log = logging.getLogger(__name__)

load_dotenv(find_dotenv(filename=".env"))
TURSO_INTERNAL_DB_URL = os.environ.get("TURSO_INTERNAL_DB_URL")
TURSO_INTERNAL_DB_AUTH_TOKEN = os.environ.get("TURSO_INTERNAL_DB_AUTH_TOKEN")

def main():
    sql = """
CREATE TRIGGER application_delete
AFTER
    DELETE ON application FOR EACH ROW BEGIN
VALUES
    (
        'application',
        OLD.id,
        json_object(
            'version',
            OLD.version,
            'name',
            OLD.name,
            'tables',
            OLD.tables
        ),
        'DELETE'
    );

END;

    """
    store = ObjectStore("result", url=TURSO_INTERNAL_DB_URL, auth_token=TURSO_INTERNAL_DB_AUTH_TOKEN)
    store.execute(sql=sql)

if __name__ == "__main__":
    main()  