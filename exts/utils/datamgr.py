import discord
import pymysql
import datetime
from enum import Enum
from functools import reduce
from typing import List, Union, NamedTuple, Dict, Optional, Any
import json
from exts.utils import errors
import os
import uuid

class AzaleaData:
    def __repr__(self):
        reprs = []
        for key, value in zip(self.__dict__.keys(), self.__dict__.values()):
            reprs.append(f'{key}={value.__repr__()}')
        reprstr = f'<{self.__class__.__name__}: ' + ' '.join(reprs) + '>'
        return reprstr

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

class Item(AzaleaData):
    """
    전체 아이템을 정의하는 클래스입니다. 예외적으로 아이템 데이터베이스 파일에서 사용되는 Item 객체에서는 self.enchantments 속성이 str입니다.
    """
    def __init__(self, id: str, name: str, description: str, max_count: int, icon: Union[str, int], tags: List[str]=[], enchantments: List[Union[Enchantment, str]]=[], meta: Dict={}, *, selling=None):
        self.id = id
        self.name = name
        self.description = description
        self.max_count = max_count
        self.icon = icon
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

class Stat(AzaleaData):
    def __init__(self, name: str, title: str):
        self.name = name
        self.title = title

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
        self, uid: str, id: int, online: bool, name: str, level: int, type: CharacterType, money: int,
        items: List[Item], stat: StatData, birth: datetime.datetime, last_nick_change: datetime.datetime,
        delete_request: Union[None, datetime.datetime], settings: List[SettingData], location: RegionData
        ):
        self.uid = uid
        self.id = id
        self.online = online
        self.name = name
        self.level = level
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
    def __init__(self, cur: pymysql.cursors.DictCursor, sdgr: SettingDBMgr, character: CharacterData):
        self.cur = cur
        self.sdgr = sdgr
        self.char = character

    def get_dict_from_settings(self, settings: List[SettingData]):
        setdict = {}
        for one in settings:
            setdict[one.name] = one.value
        return setdict

    def _save_settings(self, settings: Dict):
        return self.cur.execute('update chardata set settings=%s where name=%s', (json.dumps(settings, ensure_ascii=False), self.char.name))

    def get_setting(self, name: str) -> Any:
        sets = self.char.settings
        rawset = self.get_dict_from_settings(sets)
        setting = list(filter(lambda x: x.name == name, sets))
        if setting:
            return setting[0].value
        setting = list(filter(lambda x: x.name == name, self.sdgr.settings))
        if setting:
            setadd = self.sdgr.fetch_setting(name)
            rawset[setadd.name] = setadd.default
            self._save_settings(rawset)
            return setadd.default
        else:
            raise errors.SettingNotFound

    def edit_setting(self, name: str, value):
        sets = self.char.settings
        rawset = self.get_dict_from_settings(sets)
        setting = list(filter(lambda x: x.name == name, self.sdgr.settings))
        if setting:
            setedit = self.sdgr.fetch_setting(name)
            rawset[setedit.name] = value
            self._save_settings(rawset)
        else:
            raise errors.SettingNotFound

class NewsMgr:
    def __init__(self, cur: pymysql.cursors.DictCursor):
        self.cur = cur

    def fetch(self, limit=10):
        self.cur.execute('select * from news order by `datetime` desc limit %s', limit)
        news = self.cur.fetchall()
        newsdatas = []
        for one in news:
            newsdatas.append(NewsData(uuid.UUID(hex=one['uuid']), one['title'], one['content'], one['company'], one['datetime']))
        return newsdatas

    def publish(self, newsdata: NewsData):
        if newsdata.uid:
            uid = newsdata.uid.hex
        else:
            uid = uuid.uuid4().hex
        self.cur.execute('insert into news (uuid, datetime, title, content, company) values (%s, %s, %s, %s, %s)', (uid, newsdata.datetime, newsdata.title, newsdata.content, newsdata.company))

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

    def fetch_items_with(self, *, tags: Optional[list]=None, meta: Optional[dict]=None) -> List[Item]:
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
    def __init__(self, cur: pymysql.cursors.DictCursor, charname: str):
        self.cur = cur
        self.charname = charname

    def get_items_dict(self) -> List[Dict]:
        self.cur.execute('select items from chardata where name=%s', self.charname)
        return json.loads(self.cur.fetchone()['items'])['items']

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

    def get_items(self) -> List[ItemData]:
        items = [self.get_itemdata_from_dict(x) for x in self.get_items_dict()]
        return items

    def _save_item_by_dict(self, itemdicts: List[Dict]):
        """
        경고! 이 메서드는 캐릭터 기존의 아이템 정보를 완전히 덮어쓰게 됩니다! 자칫 아이템 데이터가 모두 삭제되거나 손상될 우려가 있습니다! 외부적 사용은 권장하지 않습니다.
        """
        items = {'items': itemdicts}
        self.cur.execute('update chardata set items=%s where name=%s', (json.dumps(items, ensure_ascii=False), self.charname))

    def delete_item(self, itemdata: ItemData, count: int= None) -> bool:
        count = int(count)
        items = self.get_items_dict()
        delitem = self.get_dict_from_itemdata(ItemData(itemdata.id, itemdata.count, itemdata.enchantments))
        if delitem in items:
            idx = items.index(delitem)
            if count == None or items[idx]['count'] - count == 0:
                items.remove(delitem)
            else:
                items[idx]['count'] -= count
            self._save_item_by_dict(items)
            return True
        return False

    def give_item(self, itemdata: ItemData):
        items = self.get_items_dict()
        giveitem = self.get_dict_from_itemdata(ItemData(itemdata.id, itemdata.count, itemdata.enchantments))
        sameitem = list(filter(lambda one: one['id'] == giveitem['id'] and one['enchantments'] == giveitem['enchantments'], items))
        if sameitem:
            idx = items.index(sameitem[0])
            items[idx]['count'] += itemdata.count
        else:
            items.append(giveitem)
        self._save_item_by_dict(items)
        return True

    @property
    def money(self):
        self.cur.execute('select money from chardata where name=%s', self.charname)
        money = self.cur.fetchone()['money']
        return money

    @money.setter
    def money(self, value):
        self.cur.execute('update chardata set money=%s where name=%s', (value, self.charname))

def get_required_exp(level: int) -> int:
    now = 1000
    for x in range(level):
        now += (-0.038*x+10)*now/100
    return round(now)

class StatMgr:
    def __init__(self, cur: pymysql.cursors.DictCursor, charname: str):
        self.cur = cur
        self.charname = charname
        self.cmgr = CharMgr(self.cur)

    def get_raw_stat(self):
        self.cur.execute('select * from statdata where name=%s', self.charname)
        statraw = self.cur.fetchone()
        return statraw
    
    def get_stat(self):
        raw = self.get_raw_stat()
        stat = StatData(
            EXP=raw['exp'],
            STR=raw['Strength'],
            INT=raw['Intelligence'],
            DEX=raw['Dexterity'],
            LUK=raw['Luck']
        )
        return stat

    @property
    def level(self):
        self.cur.execute('select level from chardata where name=%s', self.charname)
        level = self.cur.fetchone()['level']
        return level

    @level.setter
    def level(self, value):
        self.cur.execute('update chardata set level=%s where name=%s', (value, self.charname))

    @property
    def EXP(self):
        stat = self.get_stat()
        return stat.EXP

    @classmethod
    def can_levelup_count(cls, level: int, exp: int, default: int=1000):
        req = get_required_exp(level)
        count = 0
        if req <= exp:
            while req <= exp:
                count += 1
                level += 1
                req = get_required_exp(level)
        else:
            print('s')
            if exp >= 0:
                print('d')
                while req-default > exp:
                    
                    count -= 1
                    level -= 1
                    req = get_required_exp(level)
            else:
                count = -level
        return count

    def try_to_levelup(self):
        level_plus = self.can_levelup_count(self.cmgr.get_character(self.charname).level, self.EXP)
        self.level += level_plus

    @EXP.setter
    def EXP(self, value):
        self.cur.execute('update statdata set exp=%s where name=%s', (value, self.charname))
        self.try_to_levelup()

    @property
    def STR(self):
        stat = self.get_stat()
        return stat.STR

    @STR.setter
    def STR(self, value):
        self.cur.execute('update statdata set Strength=%s where name=%s', (value, self.charname))

    @property
    def INT(self):
        stat = self.get_stat()
        return stat.INT

    @INT.setter
    def INT(self, value):
        self.cur.execute('update statdata set Intelligence=%s where name=%s', (value, self.charname))

    @property
    def DEX(self):
        stat = self.get_stat()
        return stat.DEX

    @DEX.setter
    def DEX(self, value):
        self.cur.execute('update statdata set Dexterity=%s where name=%s', (value, self.charname))

    @property
    def LUK(self):
        stat = self.get_stat()
        return stat.LUK

    @LUK.setter
    def LUK(self, value):
        self.cur.execute('update statdata set Luck=%s where name=%s', (value, self.charname))

class CharMgr:
    def __init__(self, cur: pymysql.cursors.DictCursor):
        self.cur = cur

    @classmethod
    def get_char_from_dict(cls, chardict: Dict, stat: StatData) -> CharacterData:
        itemraw = json.loads(chardict['items'])['items']
        items = [ItemMgr.get_itemdata_from_dict(item) for item in itemraw]
        chartype = CharacterType.__getattr__(chardict['type'])
        setraw = json.loads(chardict['settings'])
        settings = [SettingData(setting, setraw[setting]) for setting in setraw]
        region = RegionData(chardict['location'])
        char = CharacterData(
            chardict['name'], chardict['id'], chardict['online'], chardict['name'], chardict['level'], chartype,
            chardict['money'], items, stat, chardict['birthdatetime'], chardict['last_nick_change'], chardict['delete_request'], settings, region
        )
        return char

    def get_raw_chars(self, userid: int=None) -> List[Dict]:
        if userid:
            self.cur.execute('select * from chardata where id=%s', userid)
        else:
            self.cur.execute('select * from chardata')
        rst = self.cur.fetchall()
        return rst

    def get_chars(self, userid: int=None) -> List[CharacterData]:
        raw = self.get_raw_chars(userid)
        chars = [self.get_char_from_dict(one, StatMgr(self.cur, one['name']).get_stat()) for one in raw]
        return chars

    def get_raw_character(self, name: str, userid: int=None) -> Dict:
        if userid:
            self.cur.execute('select * from chardata where id=%s and name=%s', (userid, name))
        else:
            self.cur.execute('select * from chardata where name=%s', name)
        raw = self.cur.fetchone()
        return raw

    def get_character(self, name: str, userid: int=None) -> CharacterData:
        char = self.get_raw_character(name, userid)
        if char:
            samgr = StatMgr(self.cur, char['name'])
            chardata = self.get_char_from_dict(char, samgr.get_stat())
            return chardata
        return None

    def get_current_char(self, userid: int):
        self.cur.execute('select * from chardata where id=%s and online=%s', (userid, True))
        char = self.cur.fetchone()
        samgr = StatMgr(self.cur, char['name'])
        chardata = self.get_char_from_dict(char, samgr.get_stat())
        return chardata

    def add_character_with_raw(self, userid: int, name: str, chartype: str, items, settings, level: int=1):
        datas = (
            userid, name, level, chartype,
            json.dumps(items, ensure_ascii=False),
            json.dumps(settings, ensure_ascii=False)
        )
        self.cur.execute('insert into chardata (id, name, level, type, items, settings, last_nick_change) values (%s, %s, %s, %s, %s, %s, NULL)', datas)
        self.cur.execute('insert into statdata (name) values (%s)', name)

    def logout_all(self, userid: int):
        self.cur.execute('update chardata set online=%s where id=%s and online=%s', (False, userid, True))

    def change_character(self, userid: int, name: str):
        if self.cur.execute('select * from chardata where name=%s and delete_request is not NULL', name) != 0:
            raise errors.CannotLoginBeingDeleted
        self.logout_all(userid)
        self.cur.execute('update chardata set online=%s where name=%s', (True, name))

    def delete_character(self, name: str):
        if self.cur.execute('delete from chardata where name=%s', name) == 0:
            raise errors.CharacterNotFound

    def schedule_delete(self, userid: int, name: str):
        if self.cur.execute('select * from chardata where name=%s and online=%s', (name, True)) != 0:
            self.logout_all(userid)
        if self.cur.execute('update chardata set delete_request=%s where name=%s', (datetime.datetime.now(), name)) == 0:
            raise errors.CharacterNotFound

    def cancel_delete(self, name: str):
        if self.cur.execute('update chardata set delete_request=%s where name=%s', (None, name)) == 0:
            raise errors.CharacterNotFound

    def is_being_forgotten(self, name: str):
        if (self.cur.execute('select * from chardata where name=%s', name) != 0) and self.cur.execute('select * from chardata where name=%s and delete_request is not NULL', name) != 0:
            return True
        return False

    def move_to(self, name: str, region: RegionData):
        self.cur.execute('update chardata set location=%s where name=%s', (region.name, name))

    def get_ranking(self, guild: discord.Guild=None, *, orderby='money'):
        chars = self.get_chars()
        if guild is not None:
            guildchars = list(filter(lambda one: guild.get_member(one.id) is not None, chars))
            rank = sorted(guildchars, key=lambda one: one.__getattribute__(orderby), reverse=True)
            return rank
        else:
            rank = sorted(chars, key=lambda one: one.__getattribute__(orderby), reverse=True)
            return rank