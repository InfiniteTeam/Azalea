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

    @commands.command(name='코인찬양')
    async def _thecoin(self, ctx: commands.Context):
        embed = discord.Embed(title='코인을 찬양하세요', color=self.color['primary'])
        embed.set_image(url='https://cafeptthumb-phinf.pstatic.net/MjAxODExMDdfMjQ3/MDAxNTQxNTc5MTUwMDky.9or2RpUhUHC62k2i9kwmVlAmxkJxZLmZl327_sEFfL4g.5oAHGKYn00E7EKkVHS9xvjaPk4EiCCF3AI2YNRDDK0sg.PNG.insert0012/nyan.png?type=w740')
        await ctx.send(embed=embed)

def setup(client):
    cog = Etccmds(client)
    client.add_cog(cog)