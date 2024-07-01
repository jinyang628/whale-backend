import logging
from app.models.application import Column
from app.stores.sqls.template import generate_sql_script
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine


log = logging.getLogger(__name__)

async def generate_client_table(table_name: str, columns: list[Column], db_url: str):
    sql_script = generate_sql_script(table_name=table_name, columns=columns)
    sql_statements = sql_script.split("##")
    
    engine = create_async_engine(db_url)
    async with engine.begin() as connection:
        for statement in sql_statements:
            statement = statement.strip()
            if statement:
                try:
                    # Execute each statement individually
                    await connection.execute(sqlalchemy.text(statement))
                    log.info(f"Executed SQL statement: {statement}")
                except Exception as e:
                    log.error(f"Error executing SQL statement: {e}")
                    raise
                    
    log.info(f"Table '{table_name}' created successfully")