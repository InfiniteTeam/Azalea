import discord
from discord.ext import commands
import asyncio
import datetime
import time
import math
import io
from exts.utils.basecog import BaseCog
from exts.utils import errors
import traceback

class Mastercmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.master)

    @commands.command(name='eval')
    async def _eval(self, ctx: commands.Context, *, arg):
        try:
            rst = eval(arg)
        except:
            evalout = f'📥INPUT: ```python\n{arg}```\n💥EXCEPT: ```python\n{traceback.format_exc()}```\n{self.emj.get(ctx, "cross")} ERROR'
            self.msglog.log(ctx, '[EVAL ERROR]')
        else:
            evalout = f'📥INPUT: ```python\n{arg}```\n📤OUTPUT: ```python\n{rst}```\n{self.emj.get(ctx, "check")} SUCCESS'
            self.msglog.log(ctx, '[EVAL]')
        embed=discord.Embed(title='**💬 EVAL**', color=self.color['primary'], description=evalout)
        await ctx.send(embed=embed)

    @commands.command(name='exec')
    async def _exec(self, ctx: commands.Context, *, arg):
        try:
            rst = exec(arg)
        except:
            evalout = f'📥INPUT: ```python\n{arg}```\n💥EXCEPT: ```python\n{traceback.format_exc()}```\n{self.emj.get(ctx, "cross")} ERROR'
            self.msglog.log(ctx, '[EXEC ERROR]')
        else:
            evalout = f'📥INPUT: ```python\n{arg}```\n📤OUTPUT: ```python\n{rst}```\n{self.emj.get(ctx, "check")} SUCCESS'
            self.msglog.log(ctx, '[EXEC]')
        embed=discord.Embed(title='**💬 EXEC**', color=self.color['primary'], description=evalout)
        await ctx.send(embed=embed)

    @commands.command(name='await')
    async def _await(self, ctx: commands.Context, *, arg):
        try:
            rst = await eval(arg)
        except:
            evalout = f'📥INPUT: ```python\n{arg}```\n💥EXCEPT: ```python\n{traceback.format_exc()}```\n{self.emj.get(ctx, "cross")} ERROR'
            self.msglog.log(ctx, '[AWAIT ERROR]')
        else:
            evalout = f'📥INPUT: ```python\n{arg}```\n📤OUTPUT: ```python\n{rst}```\n{self.emj.get(ctx, "check")} SUCCESS'
            self.msglog.log(ctx, '[AWAIT]')
        embed=discord.Embed(title='**💬 AWAIT**', color=self.color['primary'], description=evalout)
        await ctx.send(embed=embed)

    @commands.command(name='hawait')
    async def _hawait(self, ctx: commands.Context, *, arg):
        try:
            await eval(arg)
        except:
            await ctx.send(embed=discord.Embed(title='❌ 오류', color=self.color['error']))
            self.msglog.log(ctx, '[HAWAIT ERROR]')
        else:
            self.msglog.log(ctx, '[HAWAIT]')

    @commands.command(name='noti', aliases=['공지전송'])
    async def _noti(self, ctx: commands.Context, *args):
        try:
            title = args[0]
            desc = args[1]
        except IndexError:
            await ctx.send('공지 타이틀과 내용은 필수입니다')
            return
        imgurl = None
        if args[2]:
            imgurl = args[2]
        notiembed = discord.Embed(title=title, description=desc, color=self.color['primary'])
        notiembed.set_footer(text='작성자: ' + ctx.author.name, icon_url=ctx.author.avatar_url)
        if imgurl:
            notiembed.set_image(url=imgurl)
        preview = await ctx.send('다음과 같이 공지를 보냅니다. 계속할까요?', embed=notiembed)
        emjs = ['⭕', '❌']
        for em in emjs:
            await preview.add_reaction(em)
        self.msglog.log(ctx, '[공지전송: 미리보기]')
        def check(reaction, user):
            return user == ctx.author and preview.id == reaction.message.id and str(reaction.emoji) in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=60*5, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
            self.msglog.log(ctx, '[공지전송: 시간 초과]')
        else:
            remj = str(reaction.emoji)
            if remj == '⭕':
                pass
            elif remj == '❌':
                await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[공지전송: 취소됨]')
                return

        self.cur.execute('select * from serverdata where noticechannel is not NULL')
        guild_dbs = self.cur.fetchall()
        guild_ids = list(map(lambda one: one['id'], guild_dbs))
        guilds = list(map(lambda one: self.client.get_guild(one), guild_ids))
        guilds = list(filter(bool, guilds))
        guild_ids = list(map(lambda one: one.id, guilds))

        start = time.time()
        embed = discord.Embed(title='📢 공지 전송', description=f'전체 `{len(self.client.guilds)}`개 서버 중 `{len(guilds)}`개 서버에 전송합니다.', color=self.color['primary'])
        rst = {'suc': 0, 'exc': 0}
        logstr = ''
        embed.add_field(name='성공', value='0 서버')
        embed.add_field(name='실패', value='0 서버')

        notimsg = await ctx.send(embed=embed)
        notis = []
        for onedb in guild_dbs:
            guild = self.client.get_guild(onedb['id'])
            if not guild:
                rst['exc'] += 1
                logstr += f'서버를 찾을 수 없습니다: {onedb["id"]}\n'
                continue
            notich = guild.get_channel(onedb['noticechannel'])
            try:
                await notich.send(embed=notiembed)
            except discord.errors.Forbidden:
                rst['exc'] += 1
                logstr += f'권한이 없습니다: {guild.id}({guild.name}) 서버의 {notich.id}({notich.name}) 채널.\n'
            else:
                rst['suc'] += 1
                logstr += f'공지 전송에 성공했습니다: {guild.id}({guild.name}) 서버의 {notich.id}({notich.name}) 채널.\n'
            finally:
                embed.set_field_at(0, name='성공', value=str(rst['suc']) + ' 서버')
                embed.set_field_at(1, name='실패', value=str(rst['exc']) + ' 서버')
                await notimsg.edit(embed=embed)
        end = time.time()
        alltime = math.trunc(end - start)
        embed = discord.Embed(title=f'{self.emj.get(ctx, "check")} 공지 전송을 완료했습니다!', description='자세한 내용은 로그 파일을 참조하세요.', color=self.color['primary'])
        logfile = discord.File(fp=io.StringIO(logstr), filename='notilog.log')
        await ctx.send(embed=embed)
        await ctx.send(file=logfile)
        self.msglog.log(ctx, '[공지전송: 완료]')

    @commands.command(name='thearpa', aliases=['알파찬양'])
    async def _errortest(self, ctx: commands.Context):
        raise errors.ArpaIsGenius('알파는 천재입니다.')

    @commands.command(name='daconbabo', aliases=['다쿤바보'])
    async def _daconbabo(self, ctx: commands.Context):
        await ctx.send(self.emj.get(ctx, 'daconbabo'))

    @commands.command(name='log', aliases=['로그'])
    async def _log(self, ctx: commands.Context, arg):
        async with ctx.channel.typing():
            name = arg.lower()
            if name in ['azalea', '아젤리아']:
                f = discord.File(fp='./logs/azalea/azalea.log', filename='azalea.log')
                print('d')
                await ctx.send(file=f)
            elif name in ['ping', '핑']:
                f = discord.File(fp='./logs/ping/ping.log', filename='ping.log')
                await ctx.send(file=f)
            elif name in ['error', '에러']:
                f = discord.File(fp='./logs/error/error.log', filename='error.log')
                await ctx.send(file=f)

    @commands.command(name='sys', aliases=['실행'])
    async def _dbcmd(self, ctx: commands.Context, *, cmd):
        dbcmd = self.client.get_data('dbcmd')
        rst = await dbcmd(cmd)
        out = f'📥INPUT: ```\n{cmd}```\n📤OUTPUT: ```\n{rst}```'
        embed=discord.Embed(title='**💬 AWAIT**', color=self.color['primary'], description=out)
        await ctx.send(embed=embed)

def setup(client):
    cog = Mastercmds(client)
    client.add_cog(cog)