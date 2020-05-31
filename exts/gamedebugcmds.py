import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import json
import typing
import inspect
from exts.utils import pager, datamgr, converters
from templates import errembeds
from exts.utils.basecog import BaseCog
from exts.utils.datamgr import CharMgr, ItemMgr, ItemData, EnchantmentData, ItemDBMgr

class GameDebugcmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.master)
            cmd.add_check(self.check.char_online)

    @commands.command(name='내놔')
    async def _giveme(self, ctx: commands.Context, itemid: int, count: typing.Optional[int]=1, enchantments: commands.Greedy[converters.EnchantmentConverter]=[], charname: typing.Optional[str]=None):
        cmgr = CharMgr(self.cur)
        if charname:
            char = cmgr.get_character(charname)
            if not char :
                await ctx.send(embed=discord.Embed(title=f'❓ 존재하지 않는 캐릭터입니다!: {charname}', color=self.color['error']))
                self.msglog.log(ctx, '[아이템 받기: 존재하지 않는 캐릭터]')
                return
            charname = char.name
        else:
            charname = cmgr.get_current_char(ctx.author.id).name

        idgr = ItemDBMgr(self.datadb)
        item = idgr.fetch_item(itemid)
        embed = discord.Embed(title='📦 아이템 받기', description='다음과 같이 아이템을 받습니다. 계속할까요?', color=self.color['ask'])
        embed.add_field(name='아이템', value='[ {} ] {} {}'.format(item.id, item.icon, item.name))
        embed.add_field(name='개수', value=f'{count}개')
        enchantstrlist = [f'{enchant.name}: {enchant.level}' for enchant in enchantments]
        enchantstr = '\n'.join(enchantstrlist)
        if not enchantstr:
            enchantstr = '(없음)'
        embed.add_field(name='받는 캐릭터', value=charname)
        embed.add_field(name='마법부여', value=enchantstr, inline=False)
        msg = await ctx.send(embed=embed)

        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        self.msglog.log(ctx, '[아이템 받기: 아이템 받기]')

        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
            self.msglog.log(ctx, '[아이템 받기: 시간 초과]')
        else:
            remj = str(reaction.emoji)
            if remj == '⭕':
                imgr = ItemMgr(self.cur, charname)
                imgr.give_item(ItemData(itemid, count, enchantments))
                await ctx.send(embed=discord.Embed(title='{} 아이템을 성공적으로 받았습니다!'.format(self.emj.get(ctx, 'check')), color=self.color['success']))
                self.msglog.log(ctx, '[아이템 받기: 완료]')
            elif remj == '❌':
                await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[아이템 받기: 취소됨]')

    @_giveme.error
    async def _e_giveme(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'itemid':
                missing = '아이템 아이디'
            await ctx.send(embed=errembeds.MissingArgs.getembed(self.prefix, self.color['error'], missing))

    @commands.command(name='버려')
    async def _throw_away(self, ctx: commands.Context):
        pass

def setup(client):
    cog = GameDebugcmds(client)
    client.add_cog(cog)