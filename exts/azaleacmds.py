import discord
from discord.ext import commands
import datetime
import time
import math
import asyncio
import typing
import aiomysql
from utils.basecog import BaseCog
from utils.datamgr import NewsMgr, NewsData
from utils import pager, emojibuttons
from templates import miniembeds

class Azaleacmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            if cmd.name != '등록':
                cmd.add_check(self.check.registered)
            if cmd.name == '뉴스':
                for sub in cmd.commands:
                    if sub.name == '작성':
                        sub.add_check(self.check.has_azalea_permissions(write_news=True))

    @commands.command(name='도움', aliases=['도움말', '명령어', '명령', '커맨드', '기능'])
    async def _help(self, ctx: commands.Context):
        embed = await self.embedmgr.get(ctx, 'Help')
        if ctx.channel.type != discord.ChannelType.private:
            msg, sending = await asyncio.gather(
                ctx.author.send(embed=embed),
                ctx.send(embed=await self.embedmgr.get(ctx, 'SendingHelp'))
            )
            await sending.edit(embed=await self.embedmgr.get(ctx, 'SentHelp', msg))
        else:
            msg = await ctx.author.send(embed=embed)
        self.msglog.log(ctx, '[도움]')

    @commands.command(name='정보')
    async def _info(self, ctx: commands.Context):
        await ctx.send(embed=await self.embedmgr.get(ctx, 'Info'))
        self.msglog.log(ctx, '[정보]')

    @commands.command(name='핑', aliases=['지연시간', '레이턴시'])
    async def _ping(self, ctx: commands.Context):
        start = time.time()
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Ping', '측정하고 있어요...'))
        end = time.time()
        mlatency = math.trunc(1000 * (end - start))
        await msg.edit(embed=await self.embedmgr.get(ctx, 'Ping', '{}ms'.format(mlatency)))
        self.msglog.log(ctx, '[핑]')

    @commands.command(name='샤드')
    @commands.guild_only()
    async def _shard_id(self, ctx: commands.Context):
        await ctx.send(embed=await self.embedmgr.get(ctx, 'Shard'))
        self.msglog.log(ctx, '[샤드]')

    @commands.command(name='공지채널')
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def _notice(self, ctx: commands.Context, *, channel: typing.Optional[discord.TextChannel]=None):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                embed = await self.embedmgr.get(ctx, 'Notice_base')
                if channel:
                    notich = channel
                else:
                    notich = ctx.channel
                
                notiemjs = ['⭕', '❌']
                await cur.execute('select * from serverdata where id=%s', ctx.guild.id)
                fetch = await cur.fetchone()
                ch = ctx.guild.get_channel(fetch['noticechannel'])
                if ch:
                    if notich == ch:
                        embed = await self.embedmgr.get(ctx, 'Notice_already_this_channel')
                        notiemjs = ['⛔', '❌']
                    else:
                        embed = await self.embedmgr.get(ctx, 'Notice_selection', ch, channel, notich)
                        notiemjs = ['⭕', '⛔', '❌']
                else:
                    embed = await self.embedmgr.get(ctx, 'Notice_not_selected', channel, notich)
                msg = await ctx.send(embed=embed)
                for rct in notiemjs:
                    await msg.add_reaction(rct)
                self.msglog.log(ctx, '[공지채널: 공지채널 설정]')
                def notich_check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in notiemjs
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=60, check=notich_check)
                except asyncio.TimeoutError:
                    try:
                        await msg.clear_reactions()
                    except:
                        pass
                else:
                    em = reaction.emoji
                    if em == '⭕':
                        await cur.execute('update serverdata set noticechannel=%s where id=%s', (notich.id, ctx.guild.id))
                        await ctx.send(embed=await self.embedmgr.get(ctx, 'Notice_set_done'))
                        self.msglog.log(ctx, '[공지채널: 설정 완료]')
                    elif em == '❌':
                        await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled'))
                        self.msglog.log(ctx, '[공지채널: 취소됨]')
                    elif em == '⛔':
                        await cur.execute('update serverdata set noticechannel=%s where id=%s', (None, ctx.guild.id))
                        await ctx.send(embed=await self.embedmgr.get(ctx, 'Notice_turn_off'))
                        self.msglog.log(ctx, '[공지채널: 비활성화]')

    @commands.command(name='등록', aliases=['가입'])
    async def _register(self, ctx: commands.Context):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('select * from userdata where id=%s', ctx.author.id) != 0:
                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Register_already_registered'))
                    self.msglog.log(ctx, '[등록: 이미 등록됨]')
                    return
                
                msg = await ctx.send(content=ctx.author.mention, embed=await self.embedmgr.get(ctx, 'Register'))
                emjs = ['⭕', '❌']
                for em in emjs:
                    await msg.add_reaction(em)
                self.msglog.log(ctx, '[등록: 등록하기]')
                def check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    try:
                        await msg.clear_reactions()
                    except:
                        pass
                else:
                    remj = reaction.emoji
                    if remj == '⭕':
                        if await cur.execute('select * from userdata where id=%s', ctx.author.id) == 0:
                            if await cur.execute('insert into userdata(id, level, type) values (%s, %s, %s)', (ctx.author.id, 1, 'User')) == 1:
                                await ctx.send(embed=await self.embedmgr.get(ctx, 'Register_done'))
                                self.msglog.log(ctx, '[등록: 완료]')
                        else:
                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Register_already_registered'))
                            self.msglog.log(ctx, '[등록: 이미 등록됨]')
                    elif remj == '❌':
                        await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled'))
                        self.msglog.log(ctx, '[등록: 취소됨]')

    @commands.command(name='탈퇴')
    async def _withdraw(self, ctx: commands.Context):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                msg = await ctx.send(content=ctx.author.mention, embed=await self.embedmgr.get(ctx, 'Withdraw'))
                emjs = ['⭕', '❌']
                for em in emjs:
                    await msg.add_reaction(em)
                self.msglog.log(ctx, '[탈퇴: 탈퇴하기]')
                def check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=60, check=check)
                except asyncio.TimeoutError:
                    try:
                        await msg.clear_reactions()
                    except:
                        pass
                else:
                    remj = reaction.emoji
                    if remj == '⭕':
                        if await cur.execute('select * from userdata where id=%s', (ctx.author.id)):
                            if await cur.execute('delete from userdata where id=%s', ctx.author.id):
                                await ctx.send(embed=await self.embedmgr.get(ctx, 'Withdraw_done'))
                                self.msglog.log(ctx, '[탈퇴: 완료]')
                        else:
                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Withdraw_already'))
                            self.msglog.log(ctx, '[탈퇴: 이미 탈퇴됨]')
                    elif remj == '❌':
                        await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled'))
                        self.msglog.log(ctx, '[탈퇴: 취소됨]')

    @commands.group(name='뉴스', aliases=['신문'], invoke_without_command=True)
    async def _news(self, ctx: commands.Context):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                nmgr = NewsMgr(self.pool)
                news = await nmgr.fetch(limit=40)
                total = await cur.execute('select uuid from news')
                pgr = pager.Pager(news, 4)
                msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'News', pgr, total=total))
                self.msglog.log(ctx, '[뉴스]')
                if len(pgr.pages()) <= 1:
                    return
                for emj in emojibuttons.PageButton.emojis:
                    await msg.add_reaction(emj)
                def check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emojibuttons.PageButton.emojis
                while True:
                    try:
                        reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
                    except asyncio.TimeoutError:
                        try:
                            await msg.clear_reactions()
                        except:
                            pass
                    else:
                        do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                        if asyncio.iscoroutine(do):
                            await asyncio.gather(do,
                                msg.edit(embed=await self.embedmgr.get(ctx, 'News', pgr, total=total)),
                            )

    @_news.command(name='작성', aliases=['발행', '쓰기', '업로드'])
    async def _news_write(self, ctx: commands.Context, company, title, content: typing.Optional[str]=None):
        if content:
            if content.__len__() > 110:
                viewcontent = '> ' + content[:110] + '...\n'
            else:
                viewcontent = '> ' + content + '\n'
        else:
            viewcontent = ''
        msg = await ctx.send(
            await self.embedmgr.get(ctx, 'News_publish_continue_ask'),
            embed=await self.embedmgr.get(ctx, 'News_publish_continue', company=company, title=title, viewcontent=viewcontent)
        )
        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        self.msglog.log(ctx, '[뉴스 작성: 발행하기]')
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
        else:
            if reaction.emoji == '⭕':
                nmgr = NewsMgr(self.pool)
                await nmgr.publish(NewsData(None, title, content, company, datetime.datetime.now()))
                await ctx.send(embed=await self.embedmgr.get(ctx, 'News_publish_done'))
                self.msglog.log(ctx, '[뉴스 작성: 완료]')
            elif reaction.emoji == '❌':
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled'))
                self.msglog.log(ctx, '[뉴스 작성: 취소됨]')

    @_news_write.error
    async def _e_news_write(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'title':
                missing = '제목'
            elif error.param.name == 'content':
                missing = '내용'
            elif error.param.name == 'company':
                missing = '신문사'
            await ctx.send(embed=await self.embedmgr.get(ctx, 'MissingArgs', missing))

def setup(client):
    cog = Azaleacmds(client)
    client.add_cog(cog)