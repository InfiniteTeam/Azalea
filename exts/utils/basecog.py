import pymysql
from discord.ext import commands
from exts.utils import msglogger, checks, itemmgr, azalea, dbctrl

class BaseCog(commands.Cog):
    def __init__(self, client):
        self.client: azalea.Azalea = client
        self.config = client.get_data('config')
        self.color = client.get_data('color')
        self.emj = client.get_data('emojictrl')
        self.msglog: msglogger.Msglog = client.get_data('msglog')
        self.logger = client.get_data('logger')
        self.cur: pymysql.cursors.Cursor = client.get_data('cur')
        self.check: checks.Checks = client.get_data('check')
        self.errlogger = client.get_data('errlogger')
        self.pinglogger = client.get_data('pinglogger')
        self.templates = client.get_data('templates')
        self.dbc: dbctrl.DBctrl = client.get_data('dbc')
        self.awaiter = client.get_data('awaiter')
        self.imgr: itemmgr.ItemMgr = client.get_data('imgr')
        self.prefix = self.client.command_prefix[0]