import discord
from discord.ext import commands
import asyncio
from utils.basecog import BaseCog
from utils.gamemgr import FarmMgr
from utils.datamgr import CharMgr
from templates import errembeds
import typing

class Farmcmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            cmd.add_check(self.check.char_online)

    @commands.command(name='농장', aliases=['밭', '텃밭', '농업', '농사'])
    async def _farm(self, ctx: commands.Context, *, charname: typing.Optional[str]):
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname)
            if not char:
                await ctx.send(embed=errembeds.CharNotFound.getembed(ctx, charname))
                self.msglog.log(ctx, '[농장]: 존재하지 않는 캐릭터]')
                return
        else:
            char = await cmgr.get_current_char(ctx.author.id)
            charname = char.name

        farm_mgr = FarmMgr(self.pool, char.uid)
        level = await farm_mgr.get_level()
        embed = discord.Embed(title=f'🌲 `{char.name}` 의 농장', color=self.color['info'])
        embed.description = '**레벨** `{}`'.format(level)

        await ctx.send(embed=embed)

def setup(client):
    cog = Farmcmds(client)
    client.add_cog(cog)
