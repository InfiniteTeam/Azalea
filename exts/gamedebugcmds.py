import discord
from discord.ext import commands
import asyncio
import typing
from utils.basecog import BaseCog
from utils.datamgr import CharMgr, ItemMgr, ItemData, ItemDBMgr, StatMgr, ExpTableDBMgr

class GameDebugcmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.master)
            cmd.add_check(self.check.char_online)

    @commands.command(name='내놔')
    async def _giveme(self, ctx: commands.Context, itemid: str, count: typing.Optional[int]=1, *, charname: typing.Optional[str]=None):
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname)
            if not char :
                await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', charname))
                self.msglog.log(ctx, '[아이템 받기: 존재하지 않는 캐릭터]')
                return
            charname = char.name
        else:
            char = await cmgr.get_current_char(ctx.author.id)
            charname = char.name

        idgr = ItemDBMgr(self.datadb)
        item = idgr.fetch_item(itemid)
        if not item:
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Give_not_exists', itemid))
            return
        
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Give', item, count, char))

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
                imgr = ItemMgr(self.pool, char.uid)
                await imgr.give_item(ItemData(itemid, count))
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Give_done'))
                self.msglog.log(ctx, '[아이템 받기: 완료]')
            elif remj == '❌':
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled'))
                self.msglog.log(ctx, '[아이템 받기: 취소됨]')

    @_giveme.error
    async def _e_giveme(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'itemid':
                missing = '아이템 아이디'
            await ctx.send(embed=await self.embedmgr.get(ctx, 'MissingArgs', missing))

    @commands.command(name='경험치지급')
    async def _give_exp(self, ctx: commands.Context, exp: int, *, charname: typing.Optional[str]=None):
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname)
            if not char :
                await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', charname))
                self.msglog.log(ctx, '[경험치지급: 존재하지 않는 캐릭터]')
                return
            charname = char.name
        else:
            char = await cmgr.get_current_char(ctx.author.id)
            charname = char.name
        
        samgr = StatMgr(self.pool, char.uid, self.getlistener('on_levelup'))
        edgr = ExpTableDBMgr(self.datadb)
        stat = await samgr.get_stat()
        nowexp = stat.EXP
        lv = await samgr.get_level(edgr)
        
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Giveexp', char, nowexp, exp, lv))

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
                await samgr.give_exp(exp, edgr)
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Giveexp_done', exp))
                self.msglog.log(ctx, '[경험치지급: 완료]')
            elif reaction.emoji == '❌':
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled'))
                self.msglog.log(ctx, '[경험치지급: 취소됨]')

    @commands.command(name='계산')
    async def _clac(self, ctx: commands.Context, exp: int):
        import time
        s = time.time()
        edgr = ExpTableDBMgr(self.datadb)
        level = edgr.clac_level(exp)
        e = time.time()
        await ctx.send(f'{level}- {e-s}')

    @commands.command(name='아이디')
    async def _charid(self, ctx: commands.Context, *, charname: typing.Optional[str]=None):
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname)
            if not char:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', charname))
                self.msglog.log(ctx, '[농장: 존재하지 않는 캐릭터]')
                return
        else:
            char = await cmgr.get_current_char(ctx.author.id)
            charname = char.name

        await ctx.send(embed=discord.Embed(description=char.uid, color=self.color['info']))

def setup(client):
    cog = GameDebugcmds(client)
    client.add_cog(cog)