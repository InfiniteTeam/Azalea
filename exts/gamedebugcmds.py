import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import json
from exts.utils import pager, datacls
from exts.utils.basecog import BaseCog

class GameDebugcmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.master)
            cmd.add_check(self.check.char_online)

    @commands.command(name='ㄷ')
    async def _d(self, ctx):
        imgr = datacls.ItemMgr(self.cur, self.datadb.items, self.datadb.enchantments)
        print(imgr.fetch_item(0).enchantments[0].type)

def setup(client):
    cog = GameDebugcmds(client)
    client.add_cog(cog)