import discord
from discord.ext import commands
import asyncio
from utils.basecog import BaseCog

class Adventurecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            cmd.add_check(self.check.char_online)

    @commands.command(name='탐험')
    async def _adventure(self, ctx: commands.Context):
        print('d')

def setup(client):
    cog = Adventurecmds(client)
    client.add_cog(cog)
