import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import json
from exts.utils import pager, itemmgr
from exts.utils.basecog import BaseCog

class InGamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            if cmd.name in ['내놔']:
                cmd.add_check(self.check.master)

    def backpack_embed(self, ctx, pgr: pager.Pager):
        items = pgr.get_thispage()
        itemstr = ''
        for one in items:
            founditem = self.imgr.fetch_itemdb_by_id(one['id'])
            icon = founditem['icon']['default']
            name = founditem['name']
            itemstr += '{} {}\n'.format(icon, name)
        embed = discord.Embed(title=f'💼 `{ctx.author.name}`님의 가방', color=self.color['info'], timestamp=datetime.datetime.utcnow())
        if items:
            embed.description = itemstr + '```{}/{} 페이지```'.format(pgr.now_pagenum()+1, len(pgr.pages()))
        else:
            embed.description = '\n가방에 아무것도 없네요! ~~아, 공기는 있어요!~~'
        return embed

    @commands.command(name='가방')
    async def _backpack(self, ctx: commands.Context):
        items = self.imgr.get_useritems(ctx.author.id)
        
        print(items)
        pgr = pager.Pager(items, perpage=8)
        await ctx.send(embed=self.backpack_embed(ctx, pgr))

    @commands.command(name='내놔')
    async def _get(self, ctx: commands.Context, uid, count: int):
        print(type(count))
        self.imgr.give_item(ctx, uid, count)

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)