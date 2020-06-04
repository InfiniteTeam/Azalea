import pymysql
import datetime
from enum import Enum
from typing import List, Union, NamedTuple, Dict, Optional
import json
from exts.utils import errors
import os

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
    description: str
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
    money: int
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

    def load_enchantments(self, path: str):
        with open(path, encoding='utf-8') as dbfile:
            self.enchantments = [Enchantment(x['name'], x['max_level'], x['type'], x['tags']) for x in json.load(dbfile)['enchantments']]

    def load_items(self, path: str):
        with open(path, encoding='utf-8') as dbfile:
            items = []
            for item in json.load(dbfile)['items']:
                enchants = list(filter(
                    lambda x: set(x.tags) & set(item['tags']),
                    self.enchantments
                ))
                items.append(Item(item['id'], item['name'], item['description'], item['max_count'], item['icon']['default'], item['tags'], enchants))
            self.items = items

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

class CharMgr:
    def __init__(self, cur: pymysql.cursors.DictCursor):
        self.cur = cur

    @classmethod
    def get_char_from_dict(cls, chardict: Dict) -> CharacterData:
        itemraw = json.loads(chardict['items'])['items']
        items = [ItemMgr.get_itemdata_from_dict(item) for item in itemraw]
        stat = StatData(*json.loads(chardict['stat'])['stat'].values())
        chartype = CharacterType.__getattr__(chardict['type'])
        char = CharacterData(chardict['id'], chardict['online'], chardict['name'], chardict['level'], chartype, chardict['money'], items, stat, chardict['birthdatetime'], chardict['last_nick_change'], chardict['delete_request'])
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
            self.cur.execute('select * from chardata where id=%s and name=%s', (name, userid))
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

    def add_character_with_raw(self, userid: int, name: str, chartype: str, items, stat, level: int=1):
        datas = (
            userid, name, level, chartype,
            json.dumps(items, ensure_ascii=False),
            json.dumps(stat, ensure_ascii=False)
        )
        self.cur.execute('insert into chardata (id, name, level, type, items, stat) values (%s, %s, %s, %s, %s, %s)', datas)

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
        self.logout_all(self.get_character(name).id)
        if self.cur.execute('update chardata set delete_request=%s where name=%s', (datetime.datetime.now(), name)) == 0:
            raise errors.CharacterNotFound

    def cancel_delete(self, name: str):
        if self.cur.execute('update chardata set delete_request=%s where name=%s', (None, name)) == 0:
            raise errors.CharacterNotFound

    def is_being_forgotten(self, name: str):
        if (self.cur.execute('select * from chardata where name=%s', name) != 0) and self.cur.execute('select * from chardata where name=%s and delete_request is not NULL', name) != 0:
            return True
        return False