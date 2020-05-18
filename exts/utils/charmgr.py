import json
import datetime
from exts.utils import errors

class CharMgr:
    def __init__(self, cur, userid: int):
        self.cur = cur
        self.uid = int(userid)
    
    def get_characters(self):
        self.cur.execute('select * from chardata where id=%s order by birthdatetime asc', self.uid)
        chars = self.cur.fetchall()
        for x in chars:
            del x['id']
        return chars

    def add_character(self, name: str, chartype: str, items, level: int=1):
        self.cur.execute('insert into chardata (id, name, level, type, items) values (%s, %s, %s, %s, %s)', (self.uid, name, level, chartype, json.dumps(items, ensure_ascii=False)))

    def logout(self):
        self.cur.execute('update chardata set online=%s where online=%s', (False, True))

    def change_character(self, name: str):
        if self.cur.execute('select * from chardata where name=%s and delete_request is not NULL', name) != 0:
            raise errors.CannotLoginBeingDeleted
        self.logout()
        self.cur.execute('update chardata set online=%s where name=%s', (True, name))
        
    def delete_character(self, name: str):
        self.cur.execute('delete from chardata where name=%s', name)

    def schedule_delete(self, name: str):
        self.logout()
        self.cur.execute('update chardata set delete_request=%s where name=%s', (datetime.datetime.now(), name))

    def cancel_delete(self, name: str):
        self.cur.execute('update chardata set delete_request=%s where name=%s', (None, name))

    def is_being_forgotten(self, name: str):
        if (self.cur.execute('select * from chardata where name=%s', (name)) != 0) and self.cur.execute('select * from chardata where delete_request is not NULL') != 0:
            return True
        return False
        
class CharType:
    chartypes = {
        "Knight": "전사",
        "Archer": "궁수",
        "Wizard": "마법사",
        "God": "세계신"
    }

    @classmethod
    def Knight(cls):
        return 'Knight'
    @classmethod
    def Archer(cls):
        return 'Archer'
    @classmethod
    def Wizard(cls):
        return 'Wizard'
    @classmethod
    def God(cls):
        return 'God'

    @classmethod
    def format_chartype(cls, chartype: str):
        return cls.chartypes[chartype]