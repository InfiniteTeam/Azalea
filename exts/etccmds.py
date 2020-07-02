import discord
from discord.ext import commands
import datetime
import asyncio
import typing
from exts.utils.basecog import BaseCog

class Etccmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)

    @commands.command(name='알파찬양')
    async def _thearpa(self, ctx: commands.Context):
        f = discord.File("resources/godarpa.gif", filename="godarpa.gif")
        embed = discord.Embed(title='알파를 찬양하세요', color=self.color['primary'])
        embed.set_image(url='attachment://godarpa.gif')
        await ctx.send(file=f, embed=embed)

def setup(client):
    cog = Etccmds(client)
    client.add_cog(cog)