import json
from exts.utils import errors

class ItemDB:
    def __init__(self, cur, itemdb: list):
        self.cur = cur
        self.itemdb = itemdb

    def fetch_itemdb_by_id(self, itemid: int) -> list:
        itemid = int(itemid)
        found = list(filter(lambda item: item['id'] == itemid, self.itemdb))
        if found:
            return found[0]
        raise errors.ItemNotExistsInDB(itemid)

class ItemMgr(ItemDB):
    def __init__(self, cur, itemdb: list, userid: int):
        super().__init__(cur, itemdb)
        self.userid = userid
    
    def get_useritems(self) -> list:
        self.cur.execute('select items from chardata where id=%s and online=%s', (self.userid, True))
        items = json.loads(self.cur.fetchone()['items'])['items']
        return items

    def get_useritems_as_rawjson(self) -> dict:
        self.cur.execute('select items from chardata where id=%s and online=%s', (self.userid, True))
        items = json.loads(self.cur.fetchone()['items'])
        return items
        
    def get_item_index_exactly_same(self, item: dict):
        items = self.get_useritems()
        exactly_same_items = list(filter(
        lambda oneitem: oneitem['id'] == item['id'] and oneitem['enchantments'] == item['enchantments'], items))
        if exactly_same_items:
            return items.index(exactly_same_items[0])
        return None

    def give_item(self, uid, count: int=1, enchantments: dict=dict()):
        count = int(count)
        item = super().fetch_itemdb_by_id(uid)
        if count > item['maxcount']:
            raise errors.MaxCountExceeded(self.userid, count, item['maxcounts'])
        if not(type(count) == int and count >= 1):
            raise ValueError('아이템 개수는 자연수여야 합니다.')
        additem = {
            'id': item['id'],
            'count': count,
            'enchantments': enchantments
        }
        items = self.get_useritems_as_rawjson()
        same = self.get_item_index_exactly_same(additem)
        if same:
            items['items'][same]['count'] += count
        else:
            items['items'].append(additem)
        self.cur.execute('update chardata set items=%s where id=%s and online=%s', (json.dumps(items, ensure_ascii=False), self.userid, True))

class Item:
    def __init__(self, itemid: int, count: int, enchantments):
        pass