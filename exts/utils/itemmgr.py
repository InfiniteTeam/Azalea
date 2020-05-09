import json
from exts.utils import errors

class ItemDB:
    def __init__(self, cur, itemdb: list):
        self.cur = cur
        self.itemdb = itemdb

    def fetch_itemdb_by_id(self, uid: int) -> list:
        uid = int(uid)
        found = list(filter(lambda item: item['id'] == uid, self.itemdb))
        if found:
            return found[0]
        raise errors.ItemNotExistsInDB(uid)

class ItemMgr(ItemDB):
    def __init__(self, cur, itemdb: list):
        super().__init__(cur, itemdb)
    
    def get_useritems(self, uid: int) -> list:
        uid = int(uid)
        self.cur.execute('select items from userdata where id=%s', uid)
        items = json.loads(self.cur.fetchone()['items'])['items']
        return items

    def get_useritems_as_rawjson(self, uid: int) -> dict:
        uid = int(uid)
        self.cur.execute('select items from userdata where id=%s', uid)
        items = json.loads(self.cur.fetchone()['items'])
        return items
        
    def get_item_index_exactly_same(self, ctx, item: dict):
        items = self.get_useritems(ctx.author.id)
        exactly_same_items = list(filter(
        lambda oneitem: oneitem['id'] == item['id'] and oneitem['enchantments'] == item['enchantments'], items))
        if exactly_same_items:
            return items.index(exactly_same_items[0])
        return None

    def give_item(self, ctx, uid: int, count: int=1, enchantments: dict=dict()):
        uid = int(uid)
        count = int(count)
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
        same = self.get_item_index_exactly_same(ctx, additem)
        if same:
            items['items'][same]['count'] += count
        else:
            items['items'].append(additem)
        self.cur.execute('update userdata set items=%s where id=%s', (json.dumps(items, ensure_ascii=False), ctx.author.id))