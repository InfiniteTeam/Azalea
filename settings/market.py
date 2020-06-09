from exts.utils import datamgr

class Market:
    def __init__(self, itemdb: datamgr.ItemDBMgr):
        self.itemdb = itemdb