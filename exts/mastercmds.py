import discord
from discord.ext import commands
import asyncio
import datetime
import time
import typing
import math
import sys
import os
import io
from exts.utils.basecog import BaseCog
from exts.utils import errors, progressbar
import traceback

class Mastercmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.will_shutdown = False
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
            evalout = f'📥INPUT: ```python\n{arg}```\n{self.emj.get(ctx, "check")} SUCCESS'
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
        try:
            imgurl = args[2]
        except:
            imgurl = None
        notiembed = discord.Embed(title=title, description=desc, color=self.color['primary'], timestamp=datetime.datetime.utcnow())
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

        start = time.time()

        self.cur.execute('select * from serverdata where noticechannel is not NULL')
        guild_dbs = self.cur.fetchall()
        guilds = []
        channels = []
        for one in guild_dbs:
            guild = self.client.get_guild(one['id'])
            if guild:
                guilds.append(guild)
                channels.append(guild.get_channel(one['noticechannel']))

        cpembed = discord.Embed(title='📢 공지 전송', description=f'전체 `{len(self.client.guilds)}`개 서버 중 유효한 서버 `{len(guilds)}`개 서버에 전송합니다.', color=self.color['primary'])
        cpembed.add_field(name='진행률', value=progressbar.get(ctx, self.emj, 0, 1, 12) + ' `0.00%`', inline=False)
        cpembed.add_field(name='성공', value='0 서버')
        cpembed.add_field(name='실패', value='0 서버')
        ctrlpanel = await ctx.send(embed=cpembed)

        notilog = ''
        rst = {'suc': 0, 'exc': 0, 'done': False}
        completed = 0

        async def wrapper(coro, guild, channel):
            nonlocal notilog, rst, completed
            try:
                print('d')
                await coro
            except discord.Forbidden:
                rst['exc'] += 1
                notilog += f'권한이 없습니다: {guild.name}({guild.id}) 서버의 {channel.name}({channel.id}) 채널.\n'
            else:
                rst['suc'] += 1
                notilog += f'공지 전송에 성공했습니다: {guild.id}({guild.name}) 서버의 {channel.id}({channel.name}) 채널.\n'
            finally:
                completed += 1

        async def update_panel():
            nonlocal notilog, rst, completed
            while True:
                cpembed.set_field_at(0, name='진행률', value=progressbar.get(ctx, self.emj, completed, len(guilds), 12) + ' `{}%`'.format(round(100*(completed/len(guilds)), 2)), inline=False)
                cpembed.set_field_at(1, name='성공', value='{} 서버'.format(rst['suc']))
                cpembed.set_field_at(2, name='실패', value='{} 서버'.format(rst['exc']))
                await ctrlpanel.edit(embed=cpembed)
                print(rst['done'])
                if rst['done']:
                    break
                await asyncio.sleep(0.2)
        
        notis = []
        for guild, channel in zip(guilds, channels):
            notis.append(wrapper(channel.send(embed=notiembed), guild, channel))

        asyncio.ensure_future(update_panel())
        notisendtasks = asyncio.gather(*notis)
        await asyncio.gather(notisendtasks)
        rst['done'] = True
        end = time.time()
        alltime = round(end - start, 2)
        doneembed = discord.Embed(title=f'{self.emj.get(ctx, "check")} 공지 전송을 완료했습니다! ({alltime}초)', description='자세한 내용은 로그 파일을 참조하세요.', color=self.color['primary'])
        logfile = discord.File(fp=io.StringIO(notilog), filename='notilog.log')
        await ctx.send(embed=doneembed)
        await ctx.send(file=logfile)
        self.msglog.log(ctx, '[공지전송: 완료]')
    
    @commands.command(name='프로그레스')
    async def _progressbar(self, ctx: commands.Context, value: int, mx: int, totallen: typing.Optional[int] = 10):
        await ctx.send(embed=discord.Embed(description=progressbar.get(ctx, self.emj, value, mx, totallen)))

    @commands.command(name='프그스')
    async def _pgs(self, ctx: commands.Context):
        msg = await ctx.send(embed=discord.Embed(description=progressbar.get(ctx, self.emj, 0, 100, 20)))
        for x in range(0, 100+1, 10):
            print(x)
            await msg.edit(embed=discord.Embed(description=progressbar.get(ctx, self.emj, x, 100, 20)))
            await asyncio.sleep(0.5)

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

    @commands.group(name='master', aliases=['마스터'], invoke_without_command=False)
    async def _master(self, ctx):
        pass

    @_master.command(name='add', aliases=['추가'])
    async def _master_add(self, ctx: commands.Context, *, user: discord.Member):
        self.cur.execute('update userdata set type=%s where id=%s', ('Master', user.id))
        await ctx.send('함')

    @_master.command(name='delete', aliases=['삭제'])
    async def _master_delete(self, ctx: commands.Context, *, user: discord.Member):
        self.cur.execute('update userdata set type=%s where id=%s', ('User', user.id))
        await ctx.send('함')

    async def shutdown(self):
        self.db.close()
        await self.client.logout()

    @commands.group(name='shutdown', aliases=['셧다운', '끄기', '종료'])
    async def _shutdown(self, ctx: commands.Context, seconds: typing.Optional[float]=60.0):
        if self.will_shutdown:
            await ctx.send(embed=discord.Embed(title='❌ 이미 종료(재시작)이 예약되어 있습니다.', color=self.color['error'])) 
            return
        if math.trunc(seconds) != 0:
            now = True
            timeleftstr = f'`{seconds}초` 후에 '
        else:
            now = False
            timeleftstr = '지금 바로 '
        msg = await ctx.send(embed=discord.Embed(
            title='🖥 Azalea 종료',
            description=f'{timeleftstr}Azalea의 모든 명령어 처리 및 백그라운드 작업이 중단되고 데이터베이스 연결, SSH 연결을 닫습니다.\n**계속합니까?**',
            color=self.color['warn']
        ))
        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=20)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
        else:
            if reaction.emoji == '⭕':
                self.will_shutdown = True
                if now:
                    await ctx.send(embed=discord.Embed(title='⏳ 종료 예약됨', color=self.color['success']))
                    start = time.time()
                    async def time_left():
                        while time.time() - start < seconds and self.will_shutdown:
                            self.client.set_data('shutdown_left', seconds - (time.time() - start))
                            await asyncio.sleep(0.1)
                    await time_left()
                else:
                    await ctx.send(embed=discord.Embed(title='지금 Azalea가 종료됩니다.', color=self.color['warn']))
                if self.will_shutdown:
                    await self.shutdown()
                else:
                    self.client.set_data('shutdown_left', None)
                    await ctx.send(embed=discord.Embed(title='⏳ 종료 예약이 취소되었습니다.', color=self.color['info']))
            elif reaction.emoji == '❌':
                await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))

    @commands.command(name='재시작', aliases=['리부트', '재부팅', '리붓', '다시시작', '리스타트'])
    async def _restart(self, ctx: commands.Context, seconds: typing.Optional[float]=60.0):
        if self.will_shutdown:
            await ctx.send(embed=discord.Embed(title='❌ 이미 종료(재시작)이 예약되어 있습니다.', color=self.color['error'])) 
            return
        if math.trunc(seconds) != 0:
            now = True
            timeleftstr = f'`{seconds}초` 후에 '
        else:
            now = False
            timeleftstr = '지금 바로 '
        msg = await ctx.send(embed=discord.Embed(
            title='🖥 Azalea 재시작',
            description=f'{timeleftstr}Azalea가 완전히 종료된 후 다시 시작됩니다.\n**계속합니까?**',
            color=self.color['warn']
        ))
        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=20)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
        else:
            if reaction.emoji == '⭕':
                if now:
                    self.will_shutdown = True
                    await ctx.send(embed=discord.Embed(title='⏳ 재시작 예약됨', color=self.color['success']))
                    start = time.time()
                    async def time_left():
                        while time.time() - start < seconds and self.will_shutdown:
                            self.client.set_data('shutdown_left', seconds - (time.time() - start))
                            await asyncio.sleep(0.1)
                    await time_left()
                else:
                    await ctx.send(embed=discord.Embed(title='지금 Azalea가 재시작됩니다.', color=self.color['warn']))

                if self.will_shutdown:
                    await self.shutdown()
                    executable = sys.executable
                    args = sys.argv[:]
                    args.insert(0, sys.executable)
                    os.execvp(executable, args)
                else:
                    self.client.set_data('shutdown_left', None)
                    await ctx.send(embed=discord.Embed(title='⏳ 재시작 예약이 취소되었습니다.', color=self.color['info']))
            elif reaction.emoji == '❌':
                await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))

    @commands.command(name='종료취소')
    async def _cancel_shutdown(self, ctx: commands.Context):
        if not self.will_shutdown:
            await ctx.send(embed=discord.Embed(title='❓ 예약된 종료(재시작) 이 없습니다.', color=self.color['error']))
        self.will_shutdown = False

def setup(client):
    cog = Mastercmds(client)
    client.add_cog(cog)