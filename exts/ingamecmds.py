import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import json
from exts.utils import pager, itemmgr, emojibuttons, errors, charmgr
from exts.utils.basecog import BaseCog

class InGamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            if cmd.name != 'char':
                cmd.add_check(self.check.char_online)
            self.cnameutil.replace_name_and_aliases(cmd, cmd.name, __name__)

    async def backpack_embed(self, ctx, pgr: pager.Pager):
        items = pgr.get_thispage()
        itemstr = ''
        for one in items:
            founditem = self.imgr.fetch_itemdb_by_id(one['id'])
            icon = founditem['icon']['default']
            name = founditem['name']
            count = one['count']
            itemstr += '{} **{}** ({}개)\n'.format(icon, name, count)
        embed = discord.Embed(
            title=f'💼 `{ctx.author.name}`님의 가방',
            color=self.color['info'],
            timestamp=datetime.datetime.utcnow()
        )
        if items:
            embed.description = itemstr + '```{}/{} 페이지```'.format(pgr.now_pagenum()+1, len(pgr.pages()))
        else:
            embed.description = '\n가방에 아무것도 없네요! ~~아, 공기는 있어요!~~'
        return embed

    @commands.command(name='backpack')
    async def _backpack(self, ctx: commands.Context):
        perpage = 4
        items = self.imgr.get_useritems(ctx.author.id)
        
        print(items)
        pgr = pager.Pager(items, perpage=perpage)
        msg = await ctx.send(embed=await self.backpack_embed(ctx, pgr))
        self.msglog.log(ctx, '[가방]')
        for emj in emojibuttons.PageButton.emojis:
            await msg.add_reaction(emj)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emojibuttons.PageButton.emojis
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
            except asyncio.TimeoutError:
                pass
            else:
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                if asyncio.iscoroutine(do):
                    await asyncio.gather(do,
                        msg.edit(embed=await self.backpack_embed(ctx, pgr)),
                    )

    @commands.group(name='char')
    async def _char(self, ctx: commands.Context):
        perpage = 4
        cmgr = charmgr.CharMgr(self.cur)
        chars = cmgr.get_characters(ctx.author.id)
        if chars:
            pass
        else:
            await ctx.send(embed=discord.Embed(
                title='🎲 캐릭터가 하나도 없네요!',
                description='`{}{}` 명령으로 캐릭터를 생성해서 게임을 시작하세요!'.format(self.prefix, self.cnameutil.get_anyname('char.create')),
                color=self.color['warn'],
                timestamp=datetime.datetime.utcnow()
            ))
            

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)