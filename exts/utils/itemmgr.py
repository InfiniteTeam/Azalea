import json
from exts.utils import errors

class ItemDB:
    def __init__(self, cur, itemdb: list):
        self.cur = cur
        self.itemdb = itemdb

    def fetch_itemdb_by_id(self, uid) -> list:
        found = list(filter(lambda item: item['id'] == uid, self.itemdb))
        if found:
            return found[0]
        raise errors.ItemNotExistsInDB(uid)

class ItemMgr(ItemDB):
    def __init__(self, cur, itemdb: list):
        super().__init__(cur, itemdb)
    
    def get_useritems(self, uid: int) -> list:
        self.cur.execute('select items from userdata where id=%s', uid)
        items = json.loads(self.cur.fetchone()['items'])['items']
        return items

    def get_useritems_as_rawjson(self, uid: int) -> dict:
        self.cur.execute('select items from userdata where id=%s', uid)
        items = json.loads(self.cur.fetchone())
        return items

    def give_item(self, ctx, uid, count: int=1, enchantments: dict=dict()):
        item = super().fetch_itemdb_by_id(uid)
        if count > item['maxcount']:
            raise errors.MaxCountExceeded(uid, count, item['maxcounts'])
        if not(type(count) == int and count >= 1):
            raise ValueError('아이템 개수는 자연수여야 합니다.')
        additem = {
            'id': item['id'],
            'count': count,
            'enchantments': enchantments
        }
        items = self.get_useritems_as_rawjson(ctx.author.id)
        items['items'].append()
        self.cur.execute('update userdata set items=%s where id=%s', (additem, ctx.author.id))