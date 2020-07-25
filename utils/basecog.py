import aiomysql
import logging
from discord.ext import commands
from . import msglogger, checks, azalea, emojictrl, datamgr
import sqlite3

class BaseCog(commands.Cog):
    def __init__(self, client: azalea.Azalea):
        self.client = client
        self.config = client.get_data('config')
        self.color = client.get_data('color')
        self.emj: emojictrl.Emoji = client.get_data('emojictrl')
        self.msglog: msglogger.Msglog = client.get_data('msglog')
        self.logger: logging.Logger = client.get_data('logger')
        self.pool: aiomysql.Connection = client.get_data('pool')
        self.check: checks.Checks = client.get_data('check')
        self.errlogger = client.get_data('errlogger')
        self.pinglogger = client.get_data('pinglogger')
        self.templates = client.get_data('templates')
        self.datadb: datamgr.DataDB = client.get_data('datadb')
        self.awaiter = client.get_data('awaiter')
        self.prefix = client.command_prefix[0]
        self.eventcogname = client.get_data('eventcogname')

    def getlistener(self, name):
        listeners = self.client.get_cog(self.eventcogname).get_listeners()
        listeners_filter = list(filter(lambda x: x[0] == name, listeners))
        if listeners_filter:
            return listeners_filter[0][1]