import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import json
from exts.utils import pager, datamgr
from exts.utils.basecog import BaseCog
from exts.utils.datamgr import CharMgr, ItemMgr, ItemData, EnchantmentData

class GameDebugcmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.master)
            cmd.add_check(self.check.char_online)

    @commands.command(name='ㄷ')
    async def _d(self, ctx):
        cmgr = CharMgr(self.cur, ctx.author.id)
        imgr = ItemMgr(self.cur, 'Arpalea')
        imgr.delete_item(ItemData(id=1, count=1, enchantments=[EnchantmentData(name='ram', level=4), EnchantmentData(name='case', level=1)]))

def setup(client):
    cog = GameDebugcmds(client)
    client.add_cog(cog)