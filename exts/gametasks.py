import discord
from discord.ext import commands, tasks
import asyncio
import aiomysql
from utils.basecog import BaseCog
from utils.datamgr import FarmMgr
import datetime
import math
import time
import json

# pylint: disable=no-member

class GameTasks(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.logger.info('인게임 백그라운드 루프를 시작합니다.')
        self.process_farm.start()

    @tasks.loop(seconds=10)
    async def process_farm(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                start = time.time()
                plants = []
                await cur.execute('select * from farmdata')
                for one in await cur.fetchall():
                    rawplants = json.loads(one['plants'])['plants']
                    for x in rawplants:
                        plants.append(FarmMgr.get_plant_from_dict(x))

                end = time.time()
                # print(end-start)

    def cog_unload(self):
        self.process_farm.cancel()

    @process_farm.before_loop
    async def before_loop(self):
        await self.client.wait_until_ready()

def setup(client):
    cog = GameTasks(client)
    client.add_cog(cog)