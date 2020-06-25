from exts.utils import datamgr

class Event:
    def __init__(self, name: str):
        self.name = name

class Signal:
    pass

class ItemGiveSignal(Signal):
    def __init__(self, itemdata: datamgr.ItemData):
        self.item = itemdata