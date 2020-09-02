import discord
from discord.ext import commands
import asyncio
import aiomysql
import datetime
import random
from enum import Enum
from functools import reduce
from typing import List, Union, NamedTuple, Dict, Optional, Any, Callable, Awaitable, Tuple
import json
from . import mgrerrors
from .basemgr import AzaleaData, AzaleaManager, AzaleaDBManager
import uuid

class SettingType(Enum):
    select = 0

class Setting(AzaleaData):
    def __init__(self, name: str, title: str, description: str, type: Any, default: Any):
        self.name = name
        self.title = title
        self.description = description
        self.type = type
        self.default = default

class SettingData(AzaleaData):
    def __init__(self, name: str, value: Any):
        self.name = name
        self.value = value

class ItemType(Enum):
    Phone = '핸드폰'
    Fish = '물고기'

class Item(AzaleaData):
    """
    전체 아이템을 정의하는 클래스입니다.
    """
    def __init__(self, id: str, name: str, description: str, max_count: int, icon: Union[str, int], *, tags: List[str]=[], meta: Dict={}, selling=None):
        self.id = id
        self.name = name
        self.description = description
        self.max_count = max_count
        self.icon = icon
        self.tags = tags
        self.meta = meta
        self.selling = selling

class ItemData(AzaleaData):
    """
    한 캐릭터가 가진 아이템 하나를 나타냅니다.
    """
    def __init__(self, id: str, count: int):
        self.id = id
        self.count = count

    def __eq__(self, item):
        return self.id == item.id

class StatType(Enum):
    EXP = '경험치'
    STR = '힘'
    INT = '지력'
    DEX = '민첩'
    LUK = '운'

class StatData(AzaleaData):
    """
    한 캐릭터의 능력치 정보를 나타냅니다.
    """

    def __init__(self, *, EXP: int, STR: int, INT: int, DEX: int, LUK: int):
        self.EXP = EXP
        self.STR = STR
        self.INT = INT
        self.DEX = DEX
        self.LUK = LUK

class RegionType(Enum):
    Village = '마을'

class Region(AzaleaData):
    def __init__(self, name: str, title: str, icon: Union[str, int], type: RegionType, *, market: str, warpable: bool=False):
        self.name = name
        self.title = title
        self.icon = icon
        self.type = type
        self.market = market
        self.warpable = warpable

class RegionData(AzaleaData):
    def __init__(self, name: str):
        self.name = name

class CharacterType(Enum):
    """
    전체 캐릭터의 종류를 정의합니다.
    """
    Knight = '전사'
    Archer = '궁수'
    Wizard = '마법사'
    WorldGod = '세계신'

class CharacterData(AzaleaData):
    """
    캐릭터 하나의 정보를 나타냅니다.
    """
    def __init__(
        self, uid: str, id: int, online: bool, name: str, type: CharacterType, money: int,
        items: List[Item], stat: StatData, birth: datetime.datetime, last_nick_change: datetime.datetime,
        delete_request: Optional[datetime.datetime], settings: List[SettingData], location: RegionData
        ):
        self.uid = uid
        self.id = id
        self.online = online
        self.name = name
        self.type = type
        self.money = money
        self.items = items
        self.stat = stat
        self.birth = birth
        self.last_nick_change = last_nick_change
        self.delete_request = delete_request
        self.settings = settings
        self.location = location

class MarketItem(AzaleaData):
    def __init__(self, item: ItemData, *, price: int, discount: int = None):
        self.item = item
        self.price = price
        self.discount = discount

class NewsData(AzaleaData):
    def __init__(self, uid: Optional[uuid.UUID], title: str, content: str, company: str, datetime: datetime.datetime):
        self.uid = uid
        self.title = title
        self.content = content
        self.company = company
        self.datetime = datetime

class Permission(AzaleaData):
    def __init__(self, value: int, name: str):
        self.value = value
        self.name = name

class PermissionsData(AzaleaData):
    def __init__(self, value: int):
        self.value = value

class FarmPlantStatus(Enum):
    Growing = '자라는 중'
    AllGrownUp = '다 자람'

class FarmPlant(AzaleaData):
    def __init__(self, id: str, icon: str, title: str, grown: str, harvest_count: Tuple[int, int], *, growtime: Dict[FarmPlantStatus, Optional[Tuple[int, int]]], exp: int):
        self.id = id
        self.icon = icon
        self.title = title
        self.grown = grown
        self.harvest_count = harvest_count
        self.growtime = growtime
        self.exp = exp

class FarmPlantData(AzaleaData):
    def __init__(self, id: str, count: int, planted_datetime: datetime.datetime, grow_time: Dict):
        self.id = id
        self.count = count
        self.planted_datetime = planted_datetime
        self.grow_time = grow_time

    def __eq__(self, plant):
        return self.id == plant.id and self.count == plant.count and self.planted_datetime == plant.planted_datetime

class DataDB:
    def __init__(self):
        self.items = []
        self.char_settings = []
        self.markets = {}
        self.regions = {}
        self.permissions = []
        self.exp_table = {}
        self.farm_plants = []
        self.base_exp = {}
        self.reloader = None

    def load_items(self, items: List[Item]):
        self.items = items
    
    def load_char_settings(self, settings: List[Setting]):
        self.char_settings = settings

    def load_market(self, name, market: List[MarketItem]):
        self.markets[name] = market

    def load_region(self, name, region: List[Region]):
        self.regions[name] = region

    def load_permissions(self, perms: List[Permission]):
        self.permissions = perms

    def load_exp_table(self, table: Dict[int, int]):
        self.exp_table = table
        
    def load_farm_plants(self, plants: List[FarmPlant]):
        self.farm_plants = plants

    def load_base_exp(self, base_exp: Dict[str, int]):
        self.base_exp = base_exp

    def set_reloader(self, callback: Callable):
        self.reloader = callback

    def set_loader(self, callback: Callable):
        self.loader = callback

    def reload(self):
        self.reloader(self)

class PermDBMgr(AzaleaDBManager):
    def __init__(self, datadb: DataDB):
        self.permissions = datadb.permissions

    def get_permission(self, name: str):
        perm = list(filter(lambda x: x.name == name, self.permissions))
        if perm:
            return perm[0]

    def get_permission_by_value(self, value: int):
        perm = list(filter(lambda x: x.value == value, self.permissions))
        if perm:
            return perm[0]

class MarketDBMgr(AzaleaDBManager):
    def __init__(self, datadb: DataDB):
        self.markets = datadb.markets

    def get_market(self, name: str) -> List[MarketItem]:
        if name in self.markets:
            return self.markets[name]

class RegionDBMgr(AzaleaDBManager):
    def __init__(self, datadb: DataDB):
        self.regions = datadb.regions

    def get_world(self, world: str) -> List[Region]:
        if world in self.regions:
            return self.regions[world]

    def get_region(self, world: str, name: str) -> Region:
        if world in self.regions:
            regions = self.regions[world]
            rgn = list(filter(lambda x: x.name == name, regions))
            if rgn:
                return rgn[0]

    def get_warpables(self, world: str) -> List[Region]:
        regions = self.get_world(world)
        return list(filter(lambda x: x.warpable, regions))

class SettingDBMgr(AzaleaDBManager):
    def __init__(self, datadb: DataDB, mode='char'):
        self.settings = datadb.char_settings

    def fetch_setting(self, name: str):
        sets = list(filter(lambda x: x.name == name, self.settings))
        if sets:
            return sets[0]

    def get_base_settings(self):
        base = {}
        for one in self.settings:
            base[one.name] = one.default
        return base

class SettingMgr(AzaleaManager):
    def __init__(self, pool: aiomysql.Pool, sdgr: SettingDBMgr, charuuid: str):
        self.pool = pool
        self.sdgr = sdgr
        self.charuuid = charuuid

    @classmethod
    def get_dict_from_settings(self, settings: List[SettingData]):
        setdict = {}
        for one in settings:
            setdict[one.name] = one.value
        return setdict

    @classmethod
    def get_settings_from_dict(self, settingdict: Dict):
        sets = []
        for key, value in settingdict.items():
            sets.append(SettingData(key, value))
        return sets

    async def _save_settings(self, settings: Dict):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                rst = await cur.execute('update chardata set settings=%s where uuid=%s', (json.dumps(settings, ensure_ascii=False), self.charuuid))
                return rst

    async def get_raw_settings(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select settings from chardata where uuid=%s', self.charuuid)
                fetch = await cur.fetchone()
                raw = json.loads(fetch['settings'])
                return raw

    async def get_setting(self, name: str) -> Any:
        raw = await self.get_raw_settings()
        sets = self.get_settings_from_dict(raw)
        rawset = self.get_dict_from_settings(sets)
        setting = list(filter(lambda x: x.name == name, sets))
        if setting:
            return setting[0].value
        setting = list(filter(lambda x: x.name == name, self.sdgr.settings))
        if setting:
            setadd = self.sdgr.fetch_setting(name)
            rawset[setadd.name] = setadd.default
            await self._save_settings(rawset)
            return setadd.default
        else:
            raise mgrerrors.SettingNotFound(name)

    async def edit_setting(self, name: str, value):
        rawset = await self.get_raw_settings()
        setting = list(filter(lambda x: x.name == name, self.sdgr.settings))
        if setting:
            setedit = self.sdgr.fetch_setting(name)
            rawset[setedit.name] = value
            await self._save_settings(rawset)
        else:
            raise mgrerrors.SettingNotFound(name)

class NewsMgr(AzaleaManager):
    def __init__(self, pool: aiomysql.Pool):
        self.pool = pool

    async def fetch(self, limit=10):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select * from news order by `datetime` desc limit %s', limit)
                news = await cur.fetchall()
                newsdatas = []
                for one in news:
                    newsdatas.append(NewsData(uuid.UUID(hex=one['uuid']), one['title'], one['content'], one['company'], one['datetime']))
        return newsdatas

    async def publish(self, newsdata: NewsData):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if newsdata.uid:
                    uid = newsdata.uid.hex
                else:
                    uid = uuid.uuid4().hex
                await cur.execute('insert into news (uuid, datetime, title, content, company) values (%s, %s, %s, %s, %s)', (uid, newsdata.datetime, newsdata.title, newsdata.content, newsdata.company))

class ItemDBMgr(AzaleaDBManager):
    def __init__(self, datadb: DataDB):
        self.datadb = datadb

    def fetch_item(self, itemid: str) -> Item:
        return next((item for item in self.datadb.items if item.id == itemid), None)

    def fetch_items_with(self, *, tags: Optional[list]=None, meta: Optional[dict]=None) -> List[Item]:
        foundtags = foundmeta = set(self.datadb.items)
        if tags:
            foundtags = set(filter(lambda x: set(x.tags) & set(tags), self.datadb.items))
            if not foundtags:
                return
        if meta:
            foundmeta = set(filter(lambda x: set(meta.items()) & set(x.meta.items()), self.datadb.items))
            if not foundmeta:
                return
        rst = list(foundtags & foundmeta)
        return rst

    def get_final_selling_price(self, item: ItemData, count: int=1) -> int:
        final = self.fetch_item(item.id).selling*count
        return final

class ItemMgr(AzaleaManager):
    def __init__(self, pool: aiomysql.Pool, charuuid: str):
        self.pool = pool
        self.charuuid = charuuid

    async def get_items_dict(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select * from itemdata where charid=%s', self.charuuid)
                itms = await cur.fetchall()
        return itms

    @classmethod
    def get_itemdata_from_dict(cls, itemdict: Dict) -> ItemData:
        return ItemData(itemdict['id'], itemdict['count'])

    @classmethod
    def get_dict_from_itemdata(cls, item: ItemData) -> Dict:
        return {
            'id': item.id,
            'count': item.count
        }

    async def get_items(self) -> List[ItemData]:
        itemdict = await self.get_items_dict()
        items = [self.get_itemdata_from_dict(x) for x in itemdict]
        return items

    async def delete_item(self, itemdata: ItemData, count: int= None) -> bool:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                items = await self.get_items_dict()
                find_item = self.get_dict_from_itemdata(ItemData(itemdata.id, itemdata.count))
                delitem = next(
                    (
                        item for item in items
                        if item['id'] == find_item['id'] 
                        and item['count'] == find_item['count'] 
                    ),
                    None
                )
                if delitem is not None:
                    idx = items.index(delitem)
                    if count == None or items[idx]['count'] - count == 0:
                        await cur.execute('delete from itemdata where uuid=%s', delitem['uuid'])
                    else:
                        await cur.execute('update itemdata set count=count-%s where uuid=%s', (count, delitem['uuid']))
                else:
                    raise mgrerrors.NotFound

    async def give_item(self, itemdata: ItemData):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                items = await self.get_items_dict()
                giveitem = self.get_dict_from_itemdata(ItemData(itemdata.id, itemdata.count))
                sameitem = next((one for one in items if one['id'] == giveitem['id']), None)
                if sameitem:
                    await cur.execute('update itemdata set count=count+%s where uuid=%s', (itemdata.count, sameitem['uuid']))
                else:
                    newitemuid = uuid.uuid4().hex
                    await cur.execute('insert into itemdata (uuid, charid, id, count) values (%s, %s, %s, %s)', (
                        newitemuid, self.charuuid, itemdata.id, itemdata.count
                    ))

    async def fetch_money(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select money from chardata where uuid=%s', self.charuuid)
                fetch = await cur.fetchone()
                money = fetch['money']
        return money

    async def set_money(self, value: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('update chardata set money=%s where uuid=%s', (value, self.charuuid))

    async def give_money(self, value: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('update chardata set money=money+%s where uuid=%s', (value, self.charuuid))

class MarketMgr(AzaleaManager):
    def __init__(self, pool: aiomysql.Pool, datadb: DataDB, charuuid: str):
        self.pool = pool
        self.datadb = datadb
        self.charuuid = charuuid
        
    async def buy(self, marketitem: MarketItem, count: int):
        imgr = ItemMgr(self.pool, self.charuuid)
        money = await imgr.fetch_money()
        if marketitem.discount is None:
            final_price = count * marketitem.price
        else:
            final_price = count * marketitem.discount
        
        if final_price <= money:
            await imgr.give_money(-final_price)
            marketitem.item.count = count
            await imgr.give_item(marketitem.item)
        
    async def sell(self, item: ItemData, count: int):
        idgr = ItemDBMgr(self.datadb)
        imgr = ItemMgr(self.pool, self.charuuid)
        await imgr.delete_item(item, count)
        final_price = idgr.get_final_selling_price(item, count)
        await imgr.give_money(final_price)

class ExpTableDBMgr(AzaleaDBManager):
    def __init__(self, datadb: DataDB):
        self.datadb = datadb

    def get_required_exp(self, level: int) -> int:
        try:
            return self.datadb.exp_table[level]
        except KeyError:
            return 0

    def get_accumulate_exp(self, until_level: int) -> int:
        accumulate = [self.get_required_exp(x) for x in range(1, until_level+1)]
        return sum(accumulate)

    def clac_level(self, exp: int) -> int:
        accumulate = 0
        count = 0
        for x in range(1, len(self.datadb.exp_table)+1):
            accumulate += self.get_required_exp(x)
            if exp >= accumulate:
                count += 1
            else:
                break
        return count

class StatMgr(AzaleaManager):
    column = {
        StatType.STR: 'Strength',
        StatType.INT: 'Intelligence',
        StatType.DEX: 'Dexterity',
        StatType.LUK: 'Luck'
    }
    def __init__(self, pool: aiomysql.Pool, charuuid: str, on_levelup=None):
        """
        캐릭터의 경험치를 포함한 능력치를 관리합니다.
        on_levelup 코루틴 함수는 레벨이 상승할 때 호출되며 레벨업한 캐릭터의 uuid, 레벨업 전 레벨, 레벨업 후 레벨이 인자값으로 차례대로 전달됩니다.
        """
        self.pool = pool
        self.charuuid = charuuid
        self.cmgr = CharMgr(pool)
        self.on_levelup = on_levelup

    async def get_raw_stat(self) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select * from statdata where uuid=%s', self.charuuid)
                statraw = await cur.fetchone()
        return statraw
    
    async def get_stat(self) -> StatData:
        raw = await self.get_raw_stat()
        stat = StatData(
            EXP=raw['exp'],
            STR=raw['Strength'],
            INT=raw['Intelligence'],
            DEX=raw['Dexterity'],
            LUK=raw['Luck']
        )
        return stat

    async def get_level(self, edgr: ExpTableDBMgr) -> int:
        stat = await self.get_stat()
        exp = stat.EXP
        level = edgr.clac_level(exp)
        return level

    async def give_exp(self, value: int, edgr: ExpTableDBMgr, ctx=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                stat = await self.get_stat()
                exp = stat.EXP
                prev = edgr.clac_level(exp)
                await cur.execute('update statdata set exp=exp+%s where uuid=%s', (value, self.charuuid))
                after = edgr.clac_level(exp+value)
                if after > prev:
                    coro = self.on_levelup(self.charuuid, prev, after, ctx)
                    asyncio.create_task(coro)

    async def set_exp(self, value: int, edgr: ExpTableDBMgr, ctx=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                stat = await self.get_stat()
                exp = stat.EXP
                prev = edgr.clac_level(exp)
                await cur.execute('update statdata set exp=%s where uuid=%s', (value, self.charuuid))
                after = edgr.clac_level(value)
                if after > prev:
                    coro = self.on_levelup(self.charuuid, prev, after, ctx)
                    asyncio.create_task(coro)

    async def set_stat(self, stat: StatType, value: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                stat = self.column.get(stat)
                if stat is not None:
                    await cur.execute('update statdata set `{}`=%s where uuid=%s'.format(stat), (value, self.charuuid))

    async def give_stat(self, stat: StatType, value: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                stat = self.column.get(stat)
                if stat is not None:
                    await cur.execute('update statdata set `{name}`=`{name}`+%s where uuid=%s'.format(name=stat), (value, self.charuuid))

class CharMgr(AzaleaManager):
    def __init__(self, pool: aiomysql.Pool):
        self.pool = pool

    @classmethod
    def get_char_from_dict(cls, chardict: Dict, stat: StatData) -> CharacterData:
        itemraw = json.loads(chardict['items'])['items']
        items = [ItemMgr.get_itemdata_from_dict(item) for item in itemraw]
        chartype = CharacterType.__getattr__(chardict['type'])
        setraw = json.loads(chardict['settings'])
        settings = [SettingData(setting, setraw[setting]) for setting in setraw]
        region = RegionData(chardict['location'])
        char = CharacterData(
            chardict['uuid'], chardict['id'], chardict['online'], chardict['name'], chartype,
            chardict['money'], items, stat, chardict['birthdatetime'], chardict['last_nick_change'], chardict['delete_request'], settings, region
        )
        return char

    async def get_raw_chars(self, userid: int=None) -> List[Dict]:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if userid:
                    await cur.execute('select * from chardata where id=%s', userid)
                else:
                    await cur.execute('select * from chardata')
                rst = await cur.fetchall()
        return rst

    async def get_chars(self, userid: int=None) -> List[CharacterData]:
        raw = await self.get_raw_chars(userid)
        chars = []
        for one in raw:
            samgr = StatMgr(self.pool, one['uuid'])
            chars.append(self.get_char_from_dict(one, await samgr.get_stat()))
        return chars

    async def get_raw_character(self, charuuid: str, userid: int=None) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if userid:
                    await cur.execute('select * from chardata where id=%s and uuid=%s', (userid, charuuid))
                else:
                    await cur.execute('select * from chardata where uuid=%s', charuuid)
                raw = await cur.fetchone()
        return raw

    async def get_raw_character_by_name(self, name: str, userid: int=None) -> Dict:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if userid:
                    await cur.execute('select * from chardata where id=%s and name=%s', (userid, name))
                else:
                    await cur.execute('select * from chardata where name=%s', name)
                raw = await cur.fetchone()
        return raw

    async def get_character(self, charuuid: str, userid: int=None) -> CharacterData:
        char = await self.get_raw_character(charuuid, userid)
        if char:
            samgr = StatMgr(self.pool, char['uuid'])
            chardata = self.get_char_from_dict(char, await samgr.get_stat())
            return chardata

    async def get_character_by_name(self, name: str, userid: int=None) -> CharacterData:
        char = await self.get_raw_character_by_name(name, userid)
        if char:
            samgr = StatMgr(self.pool, char['uuid'])
            chardata = self.get_char_from_dict(char, await samgr.get_stat())
            return chardata

    async def get_current_char(self, userid: int) -> CharacterData:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select * from chardata where id=%s and online=%s', (userid, True))
                char = await cur.fetchone()
                samgr = StatMgr(self.pool, char['uuid'])
                chardata = self.get_char_from_dict(char, await samgr.get_stat())
        return chardata

    async def add_character_with_raw(self, userid: int, name: str, chartype: str, *, rollback_on_error: Optional[bool]=True, check: Optional[Callable]=None) -> CharacterData:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                uid = uuid.uuid4().hex
                datas = (
                    uid, userid, name, chartype,
                    json.dumps(
                        {'items': []},
                        ensure_ascii=False
                    ),
                    json.dumps({}, ensure_ascii=False)
                )
                try:
                    if asyncio.iscoroutine(check):
                        await check
                    elif callable(check):
                        check()
                    await cur.execute('insert into chardata (uuid, id, name, type, items, settings, last_nick_change) values (%s, %s, %s, %s, %s, %s, NULL)', datas)
                    await cur.execute('insert into statdata (uuid) values (%s)', uid)
                    
                    mine_mgr = MineMgr(self.pool, uid)
                    await mine_mgr.create_minedata()
                    farm_mgr = FarmMgr(self.pool, uid)
                    await farm_mgr.create_farmdata()

                except:
                    if rollback_on_error:
                        try:
                            await self.delete_character(uid)
                        except: pass
                    raise

                char = await self.get_character(uid)
        return char

    async def logout_all(self, userid: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('update chardata set online=%s where id=%s and online=%s', (False, userid, True))

    async def change_character(self, userid: int, charuuid: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('select * from chardata where uuid=%s and delete_request is not NULL', charuuid) != 0:
                    raise mgrerrors.CannotLoginBeingDeleted(charuuid)
                await self.logout_all(userid)
                await cur.execute('update chardata set online=%s where uuid=%s', (True, charuuid))

    async def delete_character(self, charuuid: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('delete from statdata where uuid=%s', charuuid)

                mine_mgr = MineMgr(self.pool, charuuid)
                await mine_mgr.delete_minedata()
                farm_mgr = FarmMgr(self.pool, charuuid)
                await farm_mgr.delete_farmdata()

                if await cur.execute('delete from chardata where uuid=%s', charuuid) == 0:
                    raise mgrerrors.CharacterNotFound(charuuid)

    async def change_nick(self, charuuid: str, new: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('update chardata set uuid=%s, last_nick_change=%s where uuid=%s', (new, datetime.datetime.now(), charuuid))
                await cur.execute('update statdata set uuid=%s where uuid=%s', (new, charuuid))

    async def schedule_delete(self, userid: int, charuuid: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('select * from chardata where uuid=%s and online=%s', (charuuid, True)) != 0:
                    await self.logout_all(userid)
                if await cur.execute('update chardata set delete_request=%s where uuid=%s', (datetime.datetime.now(), charuuid)) == 0:
                    raise mgrerrors.CharacterNotFound(charuuid)

    async def cancel_delete(self, charuuid: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('update chardata set delete_request=%s where uuid=%s', (None, charuuid)) == 0:
                    raise mgrerrors.CharacterNotFound(charuuid)

    async def is_being_forgotten(self, charuuid: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('select * from chardata where uuid=%s', charuuid) != 0 and await cur.execute('select * from chardata where uuid=%s and delete_request is not NULL', charuuid) != 0:
                    return True
        return False

    async def move_to(self, charuuid: str, region: RegionData):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('update chardata set location=%s where uuid=%s', (region.name, charuuid))

    async def get_ranking(self, guild: discord.Guild=None, *, orderby='money'):
        chars = await self.get_chars()
        if guild is not None:
            guildchars = list(filter(lambda one: guild.get_member(one.id) is not None, chars))
            rank = sorted(guildchars, key=lambda one: one.__getattribute__(orderby), reverse=True)
            return rank
        else:
            rank = sorted(chars, key=lambda one: one.__getattribute__(orderby), reverse=True)
            return rank

class MigrateTool:
    def __init__(self, pool: aiomysql.Pool):
        self.pool = pool

    async def copy_uuid_to_new_table(self, fetching_table: str, target_table: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f'select uuid from `{fetching_table}`')
                ls = await cur.fetchall()
                for x in ls:
                    try:
                        await cur.execute(f'insert into `{target_table}` (uuid) values (%s)', x['uuid'])
                    except:
                        pass

    async def item_json_to_row(self):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select * from chardata')
                ls = await cur.fetchall()
                for one in ls:
                    for item in json.loads(one['items'])['items']:
                        iid = uuid.uuid4().hex
                        await cur.execute('insert into itemdata (uuid, owner, id, count) values (%s, %s, %s, %s)', (
                            iid, one['uuid'], item['id'], item['count']
                        ))

class MineMgr(AzaleaManager):
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
                await cur.execute('insert into minedata (uuid) values (%s)', self.charuuid)
    
    async def delete_minedata(self):
        if not await self.has_minedata():
            return

        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('delete from minedata where uuid=%s', self.charuuid)

class FarmDBMgr(AzaleaDBManager):
    def __init__(self, datadb):
        self.datadb = datadb
        
    def fetch_plant(self, id: str) -> Optional[FarmPlant]:
        plants = list(filter(lambda x: x.id == id, self.datadb.farm_plants))
        if plants:
            return plants[0]
        return

class FarmMgr(AzaleaManager):
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
                await cur.execute('insert into farmdata (uuid, plants) values (%s, %s)', (self.charuuid, json.dumps({'plants': []}, ensure_ascii=False)))
    
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
        growtime = {}
        for k, v in plantdict['grow_time'].items():
            key = FarmPlantStatus.__dict__.get(k)
            growtime[key] = v
        plant = FarmPlantData(
            plantdict['id'],
            plantdict['count'],
            datetime.datetime.fromisoformat(plantdict['planted_datetime']),
            growtime
        )
        return plant

    @classmethod
    def get_dict_from_plant(cls, plantdata: FarmPlantData) -> Dict:
        grow_time = {}
        for k, v in plantdata.grow_time.items():
            if k is None:
                continue
            grow_time[k.name] = v
        data = {
            'id': plantdata.id,
            'count': plantdata.count,
            'planted_datetime': plantdata.planted_datetime.isoformat(),
            'grow_time': grow_time
        }
        return data
        
    async def get_raw_plants(self) -> List:
        raw = await self.get_raw_data()
        rawplants = json.loads(raw['plants'])['plants']
        return rawplants

    async def get_plants(self) -> List[FarmPlantData]:
        rawplants = await self.get_raw_plants()
        plants = [self.get_plant_from_dict(one) for one in rawplants]
        return plants
            
    async def get_level(self) -> int:
        raw = await self.get_raw_data()
        level = raw['level']
        return level

    async def get_area(self) -> int:
        raw = await self.get_raw_data()
        area = raw['area']
        return area

    @classmethod
    def get_status(cls, plantdata: FarmPlantData, when: Optional[datetime.datetime]=None) -> FarmPlantStatus:
        if not when:
            when = datetime.datetime.now()
        now = (when-plantdata.planted_datetime).total_seconds()
        
        plus = 0
        for k, v in plantdata.grow_time.items():
            plus += v
            if plus > now:
                break
        return k

    async def get_plants_with_status(self, status: FarmPlantStatus) -> List[FarmPlantData]:
        plants = await self.get_plants()
        filtered = list(filter(lambda one: self.get_status(one) == status, plants))
        return filtered
        
    async def _save_plants(self, plants: List[Dict]) -> int:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                pdt = {'plants': plants}
                rst = await cur.execute('update farmdata set plants=%s where uuid=%s', (json.dumps(pdt, ensure_ascii=False), self.charuuid))
                return rst

    async def get_used_space(self) -> int:
        return len(await self.get_raw_plants())

    async def get_free_space(self) -> int:
        area = await self.get_area()
        used = await self.get_used_space()
        return area - used
        
    async def add_plant(self, datadb: DataDB, plantid: str, count: int) -> List[FarmPlantData]:
        """
        작물을 심습니다.
        """
        farm_dmgr = FarmDBMgr(datadb)
        raw = await self.get_raw_plants()
        plantdb = farm_dmgr.fetch_plant(plantid)
        plants = []
        for one in range(count):
            grow_time = {}
            for k, v in plantdb.growtime.items():
                if v is None:
                    grow_time[k] = -1
                    break
                grow_time[k] = random.randint(v[0], v[1])
            plantdata = FarmPlantData(
                plantdb.id,
                random.randint(
                    plantdb.harvest_count[0],
                    plantdb.harvest_count[1]
                ),
                datetime.datetime.now(),
                grow_time
            )
                
            plant = self.get_dict_from_plant(plantdata)
            raw.append(plant)
            plants.append(plantdata)
        await self._save_plants(raw)
        return plants

    async def remove_plant_exact(self, *plantdata: FarmPlantData):
        if not plantdata:
            return
        plts = await self.get_plants()
        for one in plantdata:
            if one not in plts:
                raise mgrerrors.NotFound

        for one in plantdata:
            plts.remove(one)
        await self._save_plants(list(map(self.get_dict_from_plant, plts)))

    async def harvest(self, samgr: StatMgr, datadb: DataDB, *plantdata: FarmPlantData, channel_id=None):
        await self.remove_plant_exact(*plantdata)
        farm_dmgr = FarmDBMgr(datadb)
        imgr = ItemMgr(self.pool, self.charuuid)
        edgr = ExpTableDBMgr(datadb)
        exp_plus = 0
        for one in plantdata:
            plantdb = farm_dmgr.fetch_plant(one.id)
            await imgr.give_item(ItemData(plantdb.grown, one.count))
            exp_plus += datadb.base_exp.get('FARM_HARVEST')*one.count*plantdb.exp
        await samgr.give_exp(exp_plus, edgr, channel_id)