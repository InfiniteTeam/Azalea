from exts.utils.datamgr import ItemData, EnchantmentData
import typing

class IngameEvent:
    pass

class ItemGiveEvent(IngameEvent):
    def __init__(self, charname: str, item: ItemData):
        self.charname = charname
        self.item = item