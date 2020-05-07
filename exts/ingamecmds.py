import discord
from discord.ext import commands
import datetime
import asyncio
import json
from exts.utils import pager, itemmgr
from exts.utils.basecog import BaseCog

class InGamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
                cmd.add_check(self.check.registered)

    @commands.command(name='가방')
    async def _backpack(self, ctx: commands.Context):
        self.cur.execute('select items from userdata where id=%s', ctx.author.id)
        items = json.loads(self.cur.fetchone()['items'])['items']
        imgr = itemmgr.ItemMgr(self.dbs['items']['itemdb'], items)
        print(items)
        pgr = pager.Pager(items)
        

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)