import discord
from discord.ext import commands
import asyncio
import aiomysql
import pymysql
import inspect
import datetime
from enum import Enum
from functools import reduce
from typing import List, Union, NamedTuple, Dict, Optional, Any, Callable, Awaitable
import json
from . import errors
import os
import uuid

class AzaleaData:
    def __repr__(self):
        reprs = []
        for key, value in zip(self.__dict__.keys(), self.__dict__.values()):
            reprs.append(f'{key}={value.__repr__()}')
        reprstr = f'<{self.__class__.__name__}: ' + ' '.join(reprs) + '>'
        return reprstr

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

class EnchantType(Enum):
    """
    마법부여의 종류를 정의합니다.
    """
    Active = 'Active'
    Passive = 'Passive'

class Enchantment(AzaleaData):
    """
    전체 마법부여를 정의하는 클래스입니다.
    """
    def __init__(self, name: str, title: str, max_level: int, type: EnchantType, tags: List[str]=[], *, price_percent: float=1.0):
        self.name = name
        self.title = title
        self.max_level = max_level
        self.type = type
        self.tags = tags
        self.price_percent = float(price_percent)

class EnchantmentData(AzaleaData):
    """
    어떤 아이템에 부여된 마법부여 하나를 나타냅니다.
    """
    def __init__(self, name: str, level: int):
        self.name = name
        self.level = level

    def __eq__(self, enchantment):
        return self.name == enchantment.name and self.level == enchantment.level

class ItemType(Enum):
    Phone = '핸드폰'
    Fish = '물고기'

class Item(AzaleaData):
    """
    전체 아이템을 정의하는 클래스입니다. 예외적으로 아이템 데이터베이스 파일에서 사용되는 Item 객체에서는 self.enchantments 속성이 str입니다.
    """
    def __init__(self, id: str, name: str, description: str, max_count: int, icon: Union[str, int], *, type: Optional[ItemType]=None, tags: List[str]=[], enchantments: List[Union[Enchantment, str]]=[], meta: Dict={}, selling=None):
        self.id = id
        self.name = name
        self.description = description
        self.max_count = max_count
        self.icon = icon
        self.type = type
        self.tags = tags
        self.enchantments = enchantments
        self.meta = meta
        self.selling = selling

class ItemData(AzaleaData):
    """
    한 캐릭터가 가진 아이템 하나를 나타냅니다.
    """
    def __init__(self, id: str, count: int, enchantments: List[EnchantmentData]):
        self.id = id
        self.count = count
        self.enchantments = enchantments

    def __eq__(self, item):
        return self.id == item.id and self.enchantments == item.enchantments

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
    def __init__(self, name: str, title: str, icon: str, type: RegionType, *, market: str, warpable: bool=False):
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
        delete_request: Union[None, datetime.datetime], settings: List[SettingData], location: RegionData
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
    def __init__(self, uid: Union[uuid.UUID, None], title: str, content: str, company: str, datetime: datetime.datetime):
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

class DataDB:
    def __init__(self):
        self.enchantments = []
        self.items = []
        self.markets = {}
        self.regions = {}

    def load_enchantments(self, enchantments: List[Enchantment]):
        self.enchantments = enchantments

    def load_items(self, items: List[Item]):
        its = []
        for item in items:
            enchants = list(filter(
                lambda x: x.name in item.enchantments,
                self.enchantments
            ))
            item.enchantments = enchants
            its.append(item)
        self.items = its
    
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

class PermDBMgr:
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

class MarketDBMgr:
    def __init__(self, datadb: DataDB):
        self.markets = datadb.markets

    def get_market(self, name: str) -> List[MarketItem]:
        if name in self.markets:
            return self.markets[name]

class RegionDBMgr:
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

class SettingDBMgr:
    def __init__(self, datadb: DataDB, mode='char'):
        self.settings = datadb.char_settings

    def fetch_setting(self, name: str):
        sets = list(filter(lambda x: x.name == name, self.settings))
        if sets:
            return sets[0]
        return None

    def get_base_settings(self):
        base = {}
        for one in self.settings:
            base[one.name] = one.default
        return base

class SettingMgr:
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
            raise errors.SettingNotFound

    async def edit_setting(self, name: str, value):
        rawset = await self.get_raw_settings()
        setting = list(filter(lambda x: x.name == name, self.sdgr.settings))
        if setting:
            setedit = self.sdgr.fetch_setting(name)
            rawset[setedit.name] = value
            await self._save_settings(rawset)
        else:
            raise errors.SettingNotFound

class NewsMgr:
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

class ItemDBMgr:
    def __init__(self, datadb: DataDB):
        self.datadb = datadb

    def fetch_item_enchantments(self, tags: List[str]) -> Enchantment:
        enchants = []
        found = list(filter(lambda x: set(x.tags) & set(tags), self.datadb.enchantments))
        for x in found:
            enchants.append(Enchantment(x.id, x.name, x.title, x.max_level, x.type, price_percent=x.price_percent))
        return enchants

    def fetch_item(self, itemid: str) -> Item:
        found = list(filter(lambda x: x.id == itemid, self.datadb.items))
        if found:
            return found[0]
        return None

    def fetch_items_with(self, *, tags: Optional[list]=None, meta: Optional[dict]=None, type: Optional[ItemType]=None) -> List[Item]:
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

    def fetch_enchantment(self, name: str) -> Enchantment:
        found = list(filter(lambda x: name == x.name, self.datadb.enchantments))
        if found:
            return found[0]
        return None

    def get_enchantment_percent(self, item: ItemData) -> float:
        percent = reduce(lambda x, y: x*self.fetch_enchantment(y.name).price_percent, item.enchantments, 1)
        return percent

    def get_final_price(self, item: ItemData, count: int=1) -> int:
        percent = self.get_enchantment_percent(item)
        final = round(percent*self.fetch_item(item.id).selling)*count
        return final

class ItemMgr:
    def __init__(self, pool: aiomysql.Pool, charuuid: str):
        self.pool = pool
        self.charuuid = charuuid

    async def get_items_dict(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select items from chardata where uuid=%s', self.charuuid)
                fetch = await cur.fetchone()
        return json.loads(fetch['items'])['items']

    @classmethod
    def get_itemdata_from_dict(cls, itemdict: Dict) -> ItemData:
        enchants = []
        for enchant in itemdict['enchantments']:
            enchants.append(EnchantmentData(enchant, itemdict['enchantments'][enchant]))
        return ItemData(itemdict['id'], itemdict['count'], enchants)

    @classmethod
    def get_dict_from_itemdata(cls, item: ItemData) -> Dict:
        enchants = {}
        for enchant in item.enchantments:
            enchants[enchant.name] = enchant.level
            
        return {
            'id': item.id,
            'count': item.count,
            'enchantments': enchants
        }

    async def get_items(self) -> List[ItemData]:
        itemdict = await self.get_items_dict()
        items = [self.get_itemdata_from_dict(x) for x in itemdict]
        return items

    async def _save_item_by_dict(self, itemdicts: List[Dict]):
        """
        경고! 이 메서드는 캐릭터 기존의 아이템 정보를 완전히 덮어쓰게 됩니다! 자칫 아이템 데이터가 모두 삭제되거나 손상될 우려가 있습니다! 외부적 사용은 권장하지 않습니다.
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                items = {'items': itemdicts}
                await cur.execute('update chardata set items=%s where uuid=%s', (json.dumps(items, ensure_ascii=False), self.charuuid))

    async def delete_item(self, itemdata: ItemData, count: int= None) -> bool:
        count = int(count)
        items = await self.get_items_dict()
        delitem = self.get_dict_from_itemdata(ItemData(itemdata.id, itemdata.count, itemdata.enchantments))
        if delitem in items:
            idx = items.index(delitem)
            if count == None or items[idx]['count'] - count == 0:
                items.remove(delitem)
            else:
                items[idx]['count'] -= count
            await self._save_item_by_dict(items)
            return True
        return False

    async def give_item(self, itemdata: ItemData):
        items = await self.get_items_dict()
        giveitem = self.get_dict_from_itemdata(ItemData(itemdata.id, itemdata.count, itemdata.enchantments))
        sameitem = list(filter(lambda one: one['id'] == giveitem['id'] and one['enchantments'] == giveitem['enchantments'], items))
        if sameitem:
            idx = items.index(sameitem[0])
            items[idx]['count'] += itemdata.count
        else:
            items.append(giveitem)
        await self._save_item_by_dict(items)
        return True

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

class ExpTableDBMgr:
    def __init__(self, datadb: DataDB):
        self.datadb = datadb

    def get_required_exp(self, level: int) -> int:
        try:
            return self.datadb.exp_table[str(level)]
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

class StatMgr:
    column = {
        StatType.STR: 'Strength',
        StatType.INT: 'Intelligence',
        StatType.DEX: 'Dexterity',
        StatType.LUK: 'Luck'
    }
    def __init__(self, pool: aiomysql.Pool, charuuid: str, on_levelup: Callable[[str, int, int], Awaitable[Any]]=None, channel_id: int=None):
        """
        캐릭터의 경험치를 포함한 능력치를 관리합니다.
        on_levelup 어웨이터블은 레벨이 상승할 때 호출되며 레벨업한 캐릭터의 uuid, 레벨업 전 레벨, 레벨업 후 레벨이 인자값으로 차례대로 전달됩니다.
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

    async def give_exp(self, value: int, edgr: ExpTableDBMgr, channel_id=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                stat = await self.get_stat()
                exp = stat.EXP
                prev = edgr.clac_level(exp)
                await cur.execute('update statdata set exp=exp+%s where uuid=%s', (value, self.charuuid))
                after = edgr.clac_level(exp+value)
                if after > prev:
                    coro = self.on_levelup(self.charuuid, prev, after, channel_id)
                    asyncio.create_task(coro)

    async def set_exp(self, value: int, edgr: ExpTableDBMgr, channel_id=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                stat = await self.get_stat()
                exp = stat.EXP
                prev = edgr.clac_level(exp)
                await cur.execute('update statdata set exp=%s where uuid=%s', (value, self.charuuid))
                after = edgr.clac_level(value)
                if after > prev:
                    coro = self.on_levelup(self.charuuid, prev, after, channel_id)
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

class CharMgr:
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
        return None

    async def get_character_by_name(self, name: str, userid: int=None) -> CharacterData:
        char = await self.get_raw_character_by_name(name, userid)
        if char:
            samgr = StatMgr(self.pool, char['uuid'])
            chardata = self.get_char_from_dict(char, await samgr.get_stat())
            return chardata
        return None

    async def get_current_char(self, userid: int):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('select * from chardata where id=%s and online=%s', (userid, True))
                char = await cur.fetchone()
                samgr = StatMgr(self.pool, char['uuid'])
                chardata = self.get_char_from_dict(char, await samgr.get_stat())
        return chardata

    async def add_character_with_raw(self, userid: int, name: str, chartype: str, items, settings) -> CharacterData:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                uid = uuid.uuid4().hex
                datas = (
                    uid, userid, name, chartype,
                    json.dumps(items, ensure_ascii=False),
                    json.dumps(settings, ensure_ascii=False)
                )
                await cur.execute('insert into chardata (uuid, id, name, type, items, settings, last_nick_change) values (%s, %s, %s, %s, %s, %s, NULL)', datas)
                await cur.execute('insert into statdata (uuid) values (%s)', uid)
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
                    raise errors.CannotLoginBeingDeleted
                await self.logout_all(userid)
                await cur.execute('update chardata set online=%s where uuid=%s', (True, charuuid))

    async def delete_character(self, charuuid: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute('delete from statdata where uuid=%s', charuuid)
                if await cur.execute('delete from chardata where uuid=%s', charuuid) == 0:
                    raise errors.CharacterNotFound

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
                    raise errors.CharacterNotFound

    async def cancel_delete(self, charuuid: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('update chardata set delete_request=%s where uuid=%s', (None, charuuid)) == 0:
                    raise errors.CharacterNotFound

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

    async def migrate_item_id(self, itemid, newid):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                migrated = 0
                await cur.execute('select uuid, items from chardata')
                fetch = await cur.fetchall()
                for one in fetch:
                    items = json.loads(one['items'])
                    for item in items['items']:
                        if item['id'] == itemid:
                            item['id'] = newid
                            migrated += 1
                    await cur.execute('update chardata set items=%s where uuid=%s', (json.dumps(items, ensure_ascii=False), one['uuid']))
        return migrated