import discord
from discord.ext import commands
import pymysql
from enum import Enum
from typing import List, Union

class EnchantType(Enum):
    Active = 'Active'
    Passive = 'Passive'

class Enchantment:
    def __init__(self, eid: str, max_level: int, etype: Union[EnchantType, str]):
        self.id = eid
        self.max_level = max_level
        self.type = etype
        if type(etype) == str:
            self.type = list(filter(lambda x: x.value == etype, EnchantType))[0]

class EnchantmentData:
    def __init__(self, eid: str, level: int, etype: EnchantType):
        self.id = eid
        self.level = level
        self.type = etype

class Item:
    def __init__(self, itemid: int, max_count: int, enchantments: List[Enchantment]):
        self.id = itemid
        self.max_count = max_count
        self.enchantments = enchantments

class ItemMgr:
    def __init__(self, cur: pymysql.cursors.DictCursor, itemdb: dict, enchantdb: dict):
        self.cur = cur
        self.itemdb = itemdb
        self.enchantdb = enchantdb

    def fetch_item_enchantments(self, tags: List[str]) -> Enchantment:
        enchants = []
        for tag in tags:
            found = list(filter(lambda x: x == tag, self.enchantdb))
            if found:
                for x in self.enchantdb[found[0]]:
                    enchants.append(Enchantment(x['id'], x['maxlevel'], x['type']))
        return enchants

    def fetch_item(self, itemid: int):
        found = list(filter(lambda x: x['id'] == itemid, self.itemdb))
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