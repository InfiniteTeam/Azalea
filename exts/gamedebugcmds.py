import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import json
from exts.utils import pager, itemmgr
from exts.utils.basecog import BaseCog

class GameDebugcmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.master)
            cmd.add_check(self.check.char_online)
            self.cnameutil.replace_name_and_aliases(cmd, cmd.name, __name__)

    @commands.command(name='giveme')
    async def _giveme(self, ctx: commands.Context, uid: int, count: int):
        self.imgr.give_item(ctx, uid, count)

def setup(client):
    cog = GameDebugcmds(client)
    client.add_cog(cog)