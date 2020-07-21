import aiomysql
import typing

class DB:
    def __init__(self, pool: aiomysql.Pool):
        self.pool = pool
        self.conn: aiomysql.Connection = None
        self.cur: aiomysql.DictCursor = None

    async def __aenter__(self):
        self.conn = await self.pool.acquire()
        self.cur = await self.conn.cursor(aiomysql.DictCursor)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cur.close()
        self.conn.close()