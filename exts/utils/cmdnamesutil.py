import discord
from discord.ext import commands
from exts.utils import dbctrl, errors
import logging
from functools import reduce

class CmdnamesUtil:
    def __init__(self, logger: logging.Logger, dbc: dbctrl.DBctrl, filename):
        self.logger = logger
        self.dbc = dbc
        self.filename = filename

    def replace_name_and_aliases(self, cmd: commands.Command, cmdid, extname):
        try:
            cmdna = self.dbc.dbs[self.filename]['commands'][extname][cmdid]
        except KeyError:
            self.logger.warning(errors.CmdNameNotFoundInDB(extname, cmdid))
        else:
            try:
                cmd.name = cmdna['name']
            except KeyError:
                pass
            try:
                cmd.aliases = cmdna['aliases']
            except KeyError:
                pass

    def get_anyname(self, cmdid: str):
        dt = list(self.dbc.dbs[self.filename]['commands'].values())
        idsp = cmdid.split('.')
        rst = []
        for i in range(len(idsp)):
            c = '.'.join(idsp[:i+1])
            one = list(filter(lambda x: c in x.keys(), dt))[0][c]
            if 'name' in one:
                rst.append(one['name'])
            elif 'aliases' in one:
                rst.append(one['aliases'][0])
            else:
                rst.append(c)
        return ' '.join(rst)
            