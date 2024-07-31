import logging
import os

import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

EXTERNAL_DATABASE_URL = os.environ.get("EXTERNAL_DATABASE_URL")


async def execute_client_script(table_name: str, sql_script: str):
    sql_statements = sql_script.split("##")

    engine = create_async_engine(EXTERNAL_DATABASE_URL)
    async with engine.begin() as connection:
        for statement in sql_statements:
            statement = statement.strip()
            if statement:
                try:
                    await connection.execute(sqlalchemy.text(statement))
                    log.info(f"Executed SQL statement: {statement}")
                except Exception as e:
                    log.error(f"Error executing SQL statement: {e}")
                    raise

    log.info(f"Operations for table '{table_name}' completed successfully")
