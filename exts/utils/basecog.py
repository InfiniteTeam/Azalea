import pymysql
from discord.ext import commands

class BaseCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.color = client.get_data('color')
        self.emj = client.get_data('emojictrl')
        self.msglog = client.get_data('msglog')
        self.logger = client.get_data('logger')
        self.cur: pymysql.cursors.Cursor = client.get_data('cur')
        self.check = client.get_data('check')
        self.errlogger = client.get_data('errlogger')
        self.templates = client.get_data('templates')
        self.dbs = client.get_data('dbs')
        self.prefix = self.client.command_prefix