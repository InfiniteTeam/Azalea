class ItemDB:
    def __init__(self, itemdb: list):
        self.itemdb = itemdb

    def fetch_itemdb_by_id(self, uid) -> list:
        found = list(filter(lambda item: item['id'] == uid, self.itemdb))
        return found

class ItemMgr(ItemDB):
    def __init__(self, itemdb: list, useritems: list):
        super().__init__(itemdb)
        self.useritems = useritems


    