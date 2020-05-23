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

    def add_character(self, name: str, chartype: str, items, stat, level: int=1):
        datas = (
            self.uid, name, level, chartype,
            json.dumps(items, ensure_ascii=False),
            json.dumps(stat, ensure_ascii=False)
        )
        self.cur.execute('insert into chardata (id, name, level, type, items, stat) values (%s, %s, %s, %s, %s, %s)', datas)

    def logout_all(self):
        self.cur.execute('update chardata set online=%s where online=%s', (False, True))

    def change_character(self, name: str):
        if self.cur.execute('select * from chardata where name=%s and delete_request is not NULL', name) != 0:
            raise errors.CannotLoginBeingDeleted
        self.logout_all()
        self.cur.execute('update chardata set online=%s where name=%s', (True, name))
        
    def delete_character(self, name: str):
        if self.cur.execute('delete from chardata where name=%s', name) == 0:
            raise errors.CharacterNotFound

    def schedule_delete(self, name: str):
        self.logout_all()
        if self.cur.execute('update chardata set delete_request=%s where name=%s', (datetime.datetime.now(), name)) == 0:
            raise errors.CharacterNotFound

    def cancel_delete(self, name: str):
        if self.cur.execute('update chardata set delete_request=%s where name=%s', (None, name)) == 0:
            raise errors.CharacterNotFound

    def is_being_forgotten(self, name: str):
        if (self.cur.execute('select * from chardata where name=%s', name) != 0) and self.cur.execute('select * from chardata where name=%s and delete_request is not NULL', name) != 0:
            return True
        return False

    def get_char(self, name: str):
        chars = self.get_characters()
        if chars:
            return chars[0]
        return None

    def get_stats(self, name: str):
        char = self.get_char(name)
        stat = json.loads(char['stat']['stat'])

    def current_char(self):
        chars = self.get_characters()
        if chars:
            return self.get_char(chars[0]['name'])
        return None

class Character:
    def __init__(self, name: str, chartype: str, items, stat, level: int=1):
        self.name = name
        self.chartype = chartype
        self.items = items
        self.stat = stat
        self.level = level

class CharType:
    chartypes = {
        "Knight": "전사",
        "Archer": "궁수",
        "Wizard": "마법사",
        "WorldGod": "세계신"
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
    def WorldGod(cls):
        return 'WorldGod'

    @classmethod
    def format_chartype(cls, chartype: str):
        try:
            return cls.chartypes[chartype]
        except KeyError:
            return chartype