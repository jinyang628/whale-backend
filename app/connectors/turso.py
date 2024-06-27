import logging
from typing import List

import libsql_client

log = logging.getLogger(__name__)


class TursoConnector:
    url: str = None
    auth_token: str = None

    def __init__(
        self,
        url: str,
        auth_token: str,
    ):
        self.url = url
        self.auth_token = auth_token

    def execute(
        self,
        statement: libsql_client.Statement,
    ) -> libsql_client.ResultSet:
        client = libsql_client.create_client_sync(
            url=self.url,
            auth_token=self.auth_token,
        )
        try:
            logging.info(statement.sql)
            rs = client.execute(statement)
            client.close()
            return rs
        except Exception as e:
            client.close()
            raise e

    def batch_execute(
        self,
        statements: list[libsql_client.Statement],
    ) -> List[libsql_client.ResultSet]:
        client = libsql_client.create_client_sync(
            url=self.url,
            auth_token=self.auth_token,
        )

        try:
            logging.info([statement.sql for statement in statements])
            rss = client.batch(statements)
            client.close()
            return rss
        except Exception as e:
            client.close()
            raise e
