import aiomysql
from .basemgr import AzaleaData, AzaleaManager, AzaleaDBManager
from typing import Tuple, Dict, List
import json
from enum import Enum
import datetime

class AzaleaGameData(AzaleaData):
    pass

class AzaleaGameManager(AzaleaManager):
    pass

class FarmPlant(AzaleaData):
    def __init__(self, id: str, title: str, grown: str, harvest_count: Tuple[int, int], *, size: int):
        self.id = id
        self.title = title
        self.grown = grown
        self.harvest_count = harvest_count
        self.size = size

class FarmPlantStatus(Enum):
    Planted = '아직 싹이 트지 않음'
    Sprouted = '싹이 틈'
    Growing = '자라는 중'
    AllGrownUp = '다 자람'

class FarmPlantData(AzaleaData):
    def __init__(self, id: str, count: int, planted_datetime: datetime.datetime, grow_time: datetime.timedelta, status: FarmPlantStatus):
        self.id = id
        self.count = count
        self.planted_datetime = planted_datetime
        self.grow_time = grow_time
        self.status = status

class MineMgr(AzaleaGameManager):
    def __init__(self, pool: aiomysql.Pool, charuuid: str):
        self.pool = pool
        self.charuuid = charuuid

    async def has_minedata(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('select uuid from minedata where uuid=%s', self.charuuid) == 0:
                    return False
                return True
                
    async def create_minedata(self):
        if await self.has_minedata():
            return

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('insert into minedata (uuid, plants) values (%s, %s)', (self.charuuid, json.dumps({"plants": []}, ensure_ascii=False)))
    
    async def delete_minedata(self):
        if not await self.has_minedata():
            return

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('delete from minedata where uuid=%s', self.charuuid)

class FarmMgr(AzaleaGameManager):
    def __init__(self, pool: aiomysql.Pool, charuuid: str):
        self.pool = pool
        self.charuuid = charuuid

    async def has_farmdata(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('select uuid from farmdata where uuid=%s', self.charuuid) == 0:
                    return False
                return True
                
    async def create_farmdata(self):
        if await self.has_farmdata():
            return

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('insert into farmdata (uuid) values (%s)', self.charuuid)
    
    async def delete_farmdata(self):
        if not await self.has_farmdata():
            return

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('delete from farmdata where uuid=%s', self.charuuid)

    async def get_raw_data(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('select * from farmdata where uuid=%s', self.charuuid) == 0:
                    return
                raw = await cur.fetchone()
                return raw

    @classmethod
    def get_plant_from_dict(cls, plantdict: Dict) -> FarmPlantData:
        plant = FarmPlantData(
            plantdict['id'],
            plantdict['count'],
            datetime.datetime.fromisoformat(plantdict['planted_datetime']),
            datetime.timedelta(seconds=plantdict['grow_time']),
            FarmPlantStatus.__dict__.get(plantdict['status'])
        )
        return plant

    @classmethod
    def get_dict_from_plant(cls, plantdata: FarmPlantData) -> Dict:
        data = {
            'id': plantdata.id,
            'count': plantdata.count,
            'planted_datetime': plantdata.planted_datetime.isoformat(),
            'grow_time': plantdata.grow_time.total_seconds(),
            'status': plantdata.status.name
        }
        return data

    async def get_plants(self) -> List[FarmPlantData]:
        raw = await self.get_raw_data()
        rawplants = json.loads(raw['plants'])['plants']
        plants = [self.get_plant_from_dict(one) for one in rawplants]
        return plants
            
    async def get_level(self):
        raw = await self.get_raw_data()
        level = raw['level']
        return level

    async def get_area(self):
        raw = await self.get_raw_data()
        area = raw['area']
        return area

    async def get_plants_with_status(self, status: FarmPlantStatus) -> List[FarmPlantData]:
        plants = await self.get_plants()
        filtered = list(filter(lambda one: one.status == status, plants))
        return filtered