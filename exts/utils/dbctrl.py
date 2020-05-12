import os
import json

class DBctrl:
    def __init__(self, path):
        self.path = path
        dbs = {}
        for onedb in os.listdir(path):
            with open(os.path.abspath(path) + '/' + onedb, 'r', encoding='utf-8') as dbfile:
                dbs[os.path.splitext(onedb)[0]] = json.load(dbfile)
        self.dbs = dbs

    def reload(self):
        self.__init__(self.path)