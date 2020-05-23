import discord
from discord.ext import commands
import pymysql
from enum import Enum
from typing import List, Union

class DataDB:
    def __init__(self, items: list = [], enchantments: list = [], **kwargs):
        self.enchantments = enchantments
        self.items = items
        for x in kwargs:
            self.__setattr__(x, kwargs[x])

class EnchantType(Enum):
    Active = 'Active'
    Passive = 'Passive'

class Enchantment:
    def __init__(self, name: str, max_level: int, etype: Union[EnchantType, str], tags: List[str]):
        self.name = name
        self.max_level = max_level
        self.type = etype
        if type(etype) == str:
            self.type = list(filter(lambda x: x.value == etype, EnchantType))[0]
        self.tags = tags

class EnchantmentData:
    def __init__(self, name: str, level: int, etype: EnchantType, tags: List[str]):
        self.name = name
        self.level = level
        self.type = etype
        self.tags = tags

class Item:
    def __init__(self, itemid: int, max_count: int, enchantments: List[Enchantment]):
        self.id = itemid
        self.max_count = max_count
        self.enchantments = enchantments

class ItemMgr:
    def __init__(self, cur: pymysql.cursors.DictCursor, datadb: DataDB):
        self.cur = cur
        self.datadb = datadb

    def fetch_item_enchantments(self, tags: List[str]) -> Enchantment:
        enchants = []
        for tag in tags:
            found = list(filter(lambda x: x == tag, self.datadb.enchantments))
            if found:
                for x in self.enchantdb[found[0]]:
                    enchants.append(Enchantment(x['id'], x['name'], x['maxlevel'], x['type']))
        return enchants

    def fetch_item(self, itemid: int):
        found = list(filter(lambda x: x['id'] == itemid, self.datadb.items))
        if found:
            f = found[0]
            enchants = self.fetch_item_enchantments(f['tags'])
            return Item(f['id'], f['maxcount'], enchants)
        return None

class ItemData:
    def __init__(self, itemid: int, count: int, enchantments: List[Enchantment]):
        self.itemid = itemid
        self.count = count
        self.enchantments = enchantments