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
from exts.utils.datamgr import CharMgr, ItemMgr, ItemData, EnchantmentData, ItemDBMgr, StatMgr, ExpTableDBMgr

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
                await ctx.send(embed=errembeds.CharNotFound.getembed(ctx, charname))
                self.msglog.log(ctx, '[아이템 받기: 존재하지 않는 캐릭터]')
                return
            charname = char.name
        else:
            char = cmgr.get_current_char(ctx.author.id)
            charname = char.name

        idgr = ItemDBMgr(self.datadb)
        item = idgr.fetch_item(itemid)
        if not item:
            await ctx.send(embed=discord.Embed(title=f'❓ 존재하지 않는 아이템 아이디: {itemid}', color=self.color['error']))
            return
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
            reaction, user = await self.client.wait_for('reaction_add', timeout=60, check=check)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
        else:
            remj = str(reaction.emoji)
            if remj == '⭕':
                imgr = ItemMgr(self.cur, char.uid)
                imgr.give_item(ItemData(itemid, count, enchantments))
                await ctx.send(embed=discord.Embed(title='{} 아이템을 성공적으로 받았습니다!'.format(self.emj.get(ctx, 'check')), color=self.color['success']))
                self.msglog.log(ctx, '[아이템 받기: 완료]')
            elif remj == '❌':
                await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[아이템 받기: 취소됨]')

    @_giveme.error
    async def _e_giveme(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'itemid':
                missing = '아이템 아이디'
            await ctx.send(embed=errembeds.MissingArgs.getembed(self.prefix, self.color['error'], missing))

    @commands.command(name='경험치지급')
    async def _give_exp(self, ctx: commands.Context, exp: int, charname: typing.Optional[str]=None):
        cmgr = CharMgr(self.cur)
        if charname:
            char = cmgr.get_character(charname)
            if not char :
                await ctx.send(embed=errembeds.CharNotFound.getembed(ctx, charname))
                self.msglog.log(ctx, '[경험치지급: 존재하지 않는 캐릭터]')
                return
            charname = char.name
        else:
            char = cmgr.get_current_char(ctx.author.id)
            charname = char.name
        
        samgr = StatMgr(self.cur, char.uid)
        edgr = ExpTableDBMgr(self.datadb)
        nowexp = samgr.EXP
        lv = samgr.get_level(edgr)
        embed = discord.Embed(title='🏷 경험치 지급하기', description='다음과 같이 계속할까요?', color=self.color['warn'])
        embed.add_field(name='경험치 변동', value=f'{nowexp} → {nowexp+exp}')
        embed.add_field(name='레벨 변동', value='{} → {}'.format(lv, edgr.clac_level(nowexp+exp)))
        embed.add_field(name='대상 캐릭터', value=charname)
        msg = await ctx.send(embed=embed)

        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        self.msglog.log(ctx, '[경험치지급: 경험치지급]')

        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
        else:
            if reaction.emoji == '⭕':
                samgr.EXP += exp
                await ctx.send(embed=discord.Embed(title='{} 경험치 {} 만큼 성공적으로 주었습니다!'.format(self.emj.get(ctx, 'check'), exp), color=self.color['success']))
                self.msglog.log(ctx, '[경험치지급: 완료]')
            elif reaction.emoji == '❌':
                await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[경험치지급: 취소됨]')

    @commands.command(name='계산')
    async def _clac(self, ctx: commands.Context, exp: int):
        import time
        s = time.time()
        edgr = ExpTableDBMgr(self.datadb)
        level = edgr.clac_level(exp)
        e = time.time()
        await ctx.send(f'{level}- {e-s}')

def setup(client):
    cog = GameDebugcmds(client)
    client.add_cog(cog)