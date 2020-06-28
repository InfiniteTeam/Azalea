import pymysql
import datetime
from enum import Enum
from typing import List, Union, NamedTuple, Dict, Optional, Any
import json
from exts.utils import errors
import os

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
        self.default: default

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
    def __init__(self, name: str, title: str, max_level: int, type: EnchantType, tags: List[str]=[]):
        self.name = name
        self.title = title
        self.max_level = max_level
        self.type = type
        self.tags = tags

class EnchantmentData(AzaleaData):
    """
    어떤 아이템에 부여된 마법부여 하나를 나타냅니다.
    """
    def __init__(self, name: str, level: int):
        self.name = name
        self.level = level

class Item(AzaleaData):
    """
    전체 아이템을 정의하는 클래스입니다. 예외적으로 아이템 데이터베이스 파일에서 사용되는 Item 객체에서는 self.enchantments 속성이 str입니다.
    """
    def __init__(self, id: int, name: str, description: str, max_count: int, icon: Union[str, int], tags: List[str]=[], enchantments: List[Union[Enchantment, str]]=[], meta: Dict={}):
        self.id = id
        self.name = name
        self.description = description
        self.max_count = max_count
        self.icon = icon
        self.tags = tags
        self.enchantments = enchantments
        self.meta = meta

class ItemData(AzaleaData):
    """
    한 캐릭터가 가진 아이템 하나를 나타냅니다.
    """
    def __init__(self, id: int, count: int, enchantments: List[EnchantmentData]):
        self.id = id
        self.count = count
        self.enchantments = enchantments

class StatData(AzaleaData):
    """
    한 캐릭터의 능력치 정보를 나타냅니다.
    """
    def __init__(self, STR: int, INT: int, DEX: int, LUK: int):
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
        self, id: int, online: bool, name: str, level: int, type: CharacterType, money: int,
        items: List[Item], stat: StatData, birth: datetime.datetime, last_nick_change: datetime.datetime,
        delete_request: Union[None, datetime.datetime], settings: List[SettingData], location: RegionData
        ):
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
    def __init__(self, item: ItemData, price: int, selling: int, discount: int = None):
        self.item = item
        self.price = price
        self.selling = selling
        self.discount = discount

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

class MarketDBMgr:
    def __init__(self, datadb: DataDB):
        self.markets = datadb.markets

    def get_market(self, name: str):
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
    def __init__(self, cur: pymysql.cursors.Cursor, sdgr: SettingDBMgr, character: CharacterData):
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

class ItemDBMgr:
    def __init__(self, datadb: DataDB):
        self.datadb = datadb

    def fetch_item_enchantments(self, tags: List[str]) -> Enchantment:
        enchants = []
        found = list(filter(lambda x: set(x.tags) & set(tags), self.datadb.enchantments))
        for x in found:
            enchants.append(Enchantment(x.id, x.name, x.title, x.max_level, x.type))
        return enchants

    def fetch_item(self, itemid: int) -> Item:
        found = list(filter(lambda x: x.id == itemid, self.datadb.items))
        if found:
            return found[0]
        return None

    def fetch_items_with(self, tags: Optional[list]=None) -> List[Item]:
        if tags:
            found = list(filter(lambda x: set(x.tags) & set(tags), self.datadb.items))
            if found:
                return found
            return None
        return None

    def fetch_enchantment(self, name: str) -> Enchantment:
        found = list(filter(lambda x: name == x.name, self.datadb.enchantments))
        if found:
            return found[0]
        return None

class ItemMgr:
    def __init__(self, cur: pymysql.cursors.Cursor, charname: str):
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

class CharMgr:
    def __init__(self, cur: pymysql.cursors.DictCursor):
        self.cur = cur

    @classmethod
    def get_char_from_dict(cls, chardict: Dict) -> CharacterData:
        itemraw = json.loads(chardict['items'])['items']
        items = [ItemMgr.get_itemdata_from_dict(item) for item in itemraw]
        stat = StatData(*json.loads(chardict['stat'])['stat'].values())
        chartype = CharacterType.__getattr__(chardict['type'])
        setraw = json.loads(chardict['settings'])
        settings = [SettingData(setting, setraw[setting]) for setting in setraw]
        region = RegionData(chardict['location'])
        char = CharacterData(
            chardict['id'], chardict['online'], chardict['name'], chardict['level'], chartype,
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
        chars = [self.get_char_from_dict(one) for one in raw]
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
            chardata = self.get_char_from_dict(char)
            return chardata
        return None

    def get_current_char(self, userid: int):
        self.cur.execute('select * from chardata where id=%s and online=%s', (userid, True))
        char = self.cur.fetchone()
        chardata = self.get_char_from_dict(char)
        return chardata

    def add_character_with_raw(self, userid: int, name: str, chartype: str, items, stat, settings, level: int=1):
        datas = (
            userid, name, level, chartype,
            json.dumps(items, ensure_ascii=False),
            json.dumps(stat, ensure_ascii=False),
            json.dumps(settings, ensure_ascii=False)
        )
        self.cur.execute('insert into chardata (id, name, level, type, items, stat, settings) values (%s, %s, %s, %s, %s, %s, %s)', datas)

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