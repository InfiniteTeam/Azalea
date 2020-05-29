import discord
from discord.ext import commands
import pymysql
import datetime
from enum import Enum
from typing import List, Union, NamedTuple, Dict, Optional
from collections import namedtuple
import json

class EnchantType(Enum):
    """
    마법부여의 종류를 정의합니다.
    """
    Active = 'Active'
    Passive = 'Passive'

class Enchantment(NamedTuple):
    """
    전체 마법부여를 정의하는 클래스입니다.
    """
    name: str
    max_level: int
    type: EnchantType
    tags: List[str]

class EnchantmentData(NamedTuple):
    """
    어떤 아이템에 부여된 마법부여 하나를 나타냅니다.
    """
    name: str
    level: int

class Item(NamedTuple):
    """
    전체 아이템을 정의하는 클래스입니다.
    """
    id: int
    name: str
    max_count: int
    icon: str
    tags: List[str]
    enchantments: List[Enchantment]

class ItemData(NamedTuple):
    """
    한 캐릭터가 가진 아이템 하나를 나타냅니다.
    """
    id: int
    count: int
    enchantments: List[EnchantmentData]

class StatData(NamedTuple):
    """
    한 캐릭터의 능력치 정보를 나타냅니다.
    """
    STR: int
    INT: int
    DEX: int
    LUK: int

class CharacterType(Enum):
    """
    전체 캐릭터의 종류를 정의합니다.
    """
    Knight = '전사'
    Archer = '궁수'
    Wizard = '마법사'
    WorldGod = '세계신'

class CharacterData(NamedTuple):
    """
    캐릭터 하나의 정보를 나타냅니다.
    """
    id: int
    online: bool
    name: str
    level: int
    type: CharacterType
    items: List[Item]
    stat: StatData
    birth: datetime.datetime
    last_nick_change: datetime.datetime
    delete_request: Union[None, datetime.datetime]

class DataDB:
    def __init__(self, items: list = [], enchantments: list = [], **kwargs):
        self.enchantments = enchantments
        self.items = items
        for x in kwargs:
            self.__setattr__(x, kwargs[x])

class ItemDBMgr:
    def __init__(self, datadb: DataDB):
        self.datadb = datadb

    def fetch_item_enchantments(self, tags: List[str]) -> Enchantment:
        enchants = []
        found = list(filter(lambda x: set(x.tags) & set(tags), self.datadb.enchantments))
        for x in found:
            enchants.append(Enchantment(x.id, x.name, x.max_level, x.type))
        return enchants

    def fetch_item(self, itemid: int) -> Union[Item, None]:
        found = list(filter(lambda x: x.id == itemid, self.datadb.items))
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
        print(item)
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

    def delete_item(self, itemdata: ItemData) -> bool:
        items = self.get_items_dict()
        delitem = self.get_dict_from_itemdata(ItemData(itemdata.id, itemdata.count, itemdata.enchantments))
        if delitem in items:
            items.remove(delitem)
            self._save_item_by_dict(items)
            return True
        return False

class CharMgr:
    def __init__(self, cur: pymysql.cursors.DictCursor, uid: int = 0):
        self.cur = cur
        self.id = uid

    def get_raw_user_chars(self) -> List[Dict]:
        self.cur.execute('select * from chardata where id=%s', self.id)
        rst = self.cur.fetchall()
        return rst

    def get_raw_global_chars(self) -> List[Dict]:
        self.cur.execute('select * from chardata')
        rst = self.cur.fetchall()
        return rst

    def _getchars(self, mode):
        if mode == 'user':
            rst = self.get_raw_user_chars()
        elif mode == 'global':
            rst = self.get_raw_global_chars()
        chars = []
        for one in rst:
            itemraw = json.loads(one['items'])['items']
            items = [ItemMgr.get_itemdata_from_dict(item) for item in itemraw]
            stat = StatData(*json.loads(one['stat'])['stat'].values())
            chars.append(CharacterData(one['id'], one['online'], one['name'], one['level'], one['type'], items, stat, one['birthdatetime'], one['last_nick_change'], one['delete_request']))
        return chars

    def get_user_chars(self) -> List[CharacterData]:
        return self._getchars('user')
    
    def get_global_chars(self) -> List[CharacterData]:
        return self._getchars('global')

    def get_raw_user_character(self, name: str) -> Dict:
        chars = self.get_raw_user_chars()
        char = list(filter(lambda x: x['name'] == name, chars))
        if char:
            return char[0]

    def get_raw_global_character(self, name: str) -> Dict:
        chars = self.get_raw_global_chars()
        char = list(filter(lambda x: x['name'] == name, chars))
        if char:
            return char[0]

    def get_user_character(self, name: str) -> CharacterData:
        chars = self.get_user_chars()
        char = list(filter(lambda x: x.name == name, chars))
        if char:
            return char[0]
        return None

    def get_global_character(self, name: str) -> CharacterData:
        chars = self.get_global_chars()
        char = list(filter(lambda x: x.name == name, chars))
        if char:
            return char[0]
        return None
        
    def get_character_owner_id(self, charname: str) -> Union[int, None]:
        self.cur.execute('select id from chardata where name=%s', charname)
        rst = self.cur.fetchone()
        if rst:
            return rst['id']
        return None

    def get_active_character(self):
        chars = self.get_user_chars()
        char = list(filter(lambda x: x.online, chars))
        if char:
            return char[0]
        return None