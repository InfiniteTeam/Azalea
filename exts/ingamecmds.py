import discord
from discord.ext import commands
import datetime
import asyncio
from exts.utils.basecog import BaseCog

class InGamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
                cmd.add_check(self.check.registered)

    @commands.command(name='아이템')
    async def _myitem(self, ctx: commands.Context):
        pass

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)