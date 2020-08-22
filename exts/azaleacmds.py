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
from templates import miniembeds, azaleaembeds

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
                embed = embed = discord.Embed(
                    title='📢 공지채널 설정',
                    description='',
                    color=self.color['ask']
                )
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
                        embed = discord.Embed(
                            title=f'❓ 이미 이 채널이 공지채널로 설정되어 있습니다!',
                            description='',
                            color=self.color['ask']
                        )
                        
                        notiemjs = ['⛔', '❌']
                    else:
                        embed.description = f'**현재 공지채널은 {ch.mention} 로 설정되어 있습니다.**'
                        if channel:
                            embed.description += f'\n{notich.mention} 을 공지채널로 설정할까요?'
                        else:
                            embed.description += '\n현재 채널을 공지채널로 설정할까요?'
                        notiemjs = ['⭕', '⛔', '❌']
                    embed.description += '\n공지를 끄려면 ⛔ 로 반응해주세요! 취소하려면 ❌ 로 반응해주세요.'
                else:
                    embed.description = f'**이 서버에는 공지채널이 설정되어있지 않아 공지가 꺼져있습니다.**'
                    if channel:
                        embed.description += f'\n{notich.mention} 을 공지채널로 설정할까요?'
                    else:
                        embed.description += '\n현재 채널을 공지채널로 설정할까요?'
                msg = await ctx.send(embed=embed)
                for rct in notiemjs:
                    await msg.add_reaction(rct)
                self.msglog.log(ctx, '[공지채널: 공지채널 설정]')
                def notich_check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in notiemjs
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=20, check=notich_check)
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
                    self.msglog.log(ctx, '[공지채널: 시간 초과]')
                else:
                    em = reaction.emoji
                    if em == '⭕':
                        await cur.execute('update serverdata set noticechannel=%s where id=%s', (notich.id, ctx.guild.id))
                        await ctx.send(embed=discord.Embed(title=f'{self.emj.get(ctx, "check")} 공지 채널을 성공적으로 설정했습니다!', description=f'이제 {notich.mention} 채널에 공지를 보냅니다.', color=self.color['info']))
                        self.msglog.log(ctx, '[공지채널: 설정 완료]')
                    elif em == '❌':
                        await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
                        self.msglog.log(ctx, '[공지채널: 취소됨]')
                    elif em == '⛔':
                        await cur.execute('update serverdata set noticechannel=%s where id=%s', (None, ctx.guild.id))
                        await ctx.send(embed=discord.Embed(title=f'❌ 공지 기능을 껐습니다!', color=self.color['error']))
                        self.msglog.log(ctx, '[공지채널: 비활성화]')

    @commands.command(name='등록', aliases=['가입'])
    async def _register(self, ctx: commands.Context):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if await cur.execute('select * from userdata where id=%s', ctx.author.id) != 0:
                    await ctx.send(embed=discord.Embed(title=f'{self.emj.get(ctx, "check")} 이미 등록된 사용자입니다!', color=self.color['info']))
                    self.msglog.log(ctx, '[등록: 이미 등록됨]')
                    return
                embed = discord.Embed(title='Azalea 등록', description='**Azalea를 이용하기 위한 이용약관 및 개인정보 취급방침입니다. Azalea를 이용하려면 동의가 필요 합니다.**', color=self.color['ask'])
                embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
                embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
                msg = await ctx.send(content=ctx.author.mention, embed=embed)
                emjs = ['⭕', '❌']
                for em in emjs:
                    await msg.add_reaction(em)
                self.msglog.log(ctx, '[등록: 등록하기]')
                def check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=20.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
                    self.msglog.log(ctx, '[등록: 시간 초과]')
                else:
                    remj = reaction.emoji
                    if remj == '⭕':
                        if await cur.execute('select * from userdata where id=%s', ctx.author.id) == 0:
                            if await cur.execute('insert into userdata(id, level, type) values (%s, %s, %s)', (ctx.author.id, 1, 'User')) == 1:
                                await ctx.send('등록되었습니다. `{}도움` 명령으로 전체 명령을 볼 수 있습니다.'.format(self.prefix))
                                self.msglog.log(ctx, '[등록: 완료]')
                        else:
                            await ctx.send(embed=discord.Embed(title=f'{self.emj.get(ctx, "check")} 이미 등록된 사용자입니다!', color=self.color['info']))
                            self.msglog.log(ctx, '[등록: 이미 등록됨]')
                    elif remj == '❌':
                        await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
                        self.msglog.log(ctx, '[등록: 취소됨]')

    @commands.command(name='탈퇴')
    async def _withdraw(self, ctx: commands.Context):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                embed = discord.Embed(title='Azalea 탈퇴',
                description='''**Azalea 이용약관 및 개인정보 취급방침 동의를 철회하고, Azalea를 탈퇴하게 됩니다.**
                이 경우 _사용자님의 모든 데이터(개인정보 취급방침을 참조하십시오)_가 Azalea에서 삭제되며, __되돌릴 수 없습니다.__
                계속할까요?''', color=self.color['warn'])
                embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
                embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
                msg = await ctx.send(content=ctx.author.mention, embed=embed)
                emjs = ['⭕', '❌']
                for em in emjs:
                    await msg.add_reaction(em)
                self.msglog.log(ctx, '[탈퇴: 탈퇴하기]')
                def check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=20.0, check=check)
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
                    self.msglog.log(ctx, '[탈퇴: 시간 초과]')
                else:
                    remj = reaction.emoji
                    if remj == '⭕':
                        if await cur.execute('select * from userdata where id=%s', (ctx.author.id)):
                            if await cur.execute('delete from userdata where id=%s', ctx.author.id):
                                await ctx.send('탈퇴되었습니다.')
                                self.msglog.log(ctx, '[탈퇴: 완료]')
                        else:
                            await ctx.send('이미 탈퇴된 사용자입니다.')
                            self.msglog.log(ctx, '[탈퇴: 이미 탈퇴됨]')
                    elif remj == '❌':
                        await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
                        self.msglog.log(ctx, '[탈퇴: 취소됨]')

    @commands.group(name='뉴스', aliases=['신문'], invoke_without_command=True)
    async def _news(self, ctx: commands.Context):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                nmgr = NewsMgr(self.pool)
                news = await nmgr.fetch(limit=40)
                total = await cur.execute('select uuid from news')
                pgr = pager.Pager(news, 4)
                msg = await ctx.send(embed=await azaleaembeds.news_embed(self, pgr, total=total))
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
                                msg.edit(embed=await azaleaembeds.news_embed(self, pgr, total=total)),
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
        embed = discord.Embed(title='📰 뉴스', color=self.color['info'])
        embed.description = f'🔹 **`{title}`**\n{viewcontent}**- {company}**, 방금'
        embed.set_author(name='뉴스 발행 미리보기')
        msg = await ctx.send('{} 다음과 같이 발행할까요?'.format(ctx.author.mention), embed=embed)
        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        self.msglog.log(ctx, '[뉴스 작성: 발행하기]')
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=20.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
            self.msglog.log(ctx, '[뉴스 작성: 시간 초과]')
        else:
            if reaction.emoji == '⭕':
                nmgr = NewsMgr(self.pool)
                await nmgr.publish(NewsData(None, title, content, company, datetime.datetime.now()))
                await ctx.send(embed=discord.Embed(
                    title='{} 발행되었습니다.'.format(self.emj.get(ctx, 'check')), color=self.color['success']
                ))
                self.msglog.log(ctx, '[뉴스 작성: 완료]')
            elif reaction.emoji == '❌':
                await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
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
            await ctx.send(embed=miniembeds.MissingArgs.getembed(self.prefix, self.color['error'], missing))

def setup(client):
    cog = Azaleacmds(client)
    client.add_cog(cog)