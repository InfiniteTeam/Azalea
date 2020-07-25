import discord
from discord.ext import commands
import asyncio
from utils.basecog import BaseCog

class Minecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            cmd.add_check(self.check.char_online)

    async def cog_before_invoke(self, ctx: commands.Context):
        print(self.getlistener('on_command_error'))
        await asyncio.sleep(1)

    @commands.command(name='광산')
    async def _mine(self, ctx: commands.Context):
        print('d')

def setup(client):
    cog = Minecmds(client)
    client.add_cog(cog)
