class CharMgr:
    def __init__(self, cur):
        self.cur = cur
    
    def get_characters(self, userid: int):
        userid = int(userid)
        self.cur.execute('select * from chardata where id=%s', userid)