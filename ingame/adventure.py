from exts.utils import datamgr
import typing

class Event:
    def __init__(self, name: str, check=None):
        self.name = name

    def do(self):
        pass

class Signal:
    pass

class ItemGiveSignal(Signal):
    def __init__(self, itemdata: datamgr.ItemData):
        self.item = itemdata

