import discord
from discord.ext import commands
from exts.utils import dbctrl, errors
import logging

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