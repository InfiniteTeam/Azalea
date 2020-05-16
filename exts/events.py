import discord
from discord.ext import commands
import traceback
import datetime
import io
import sys
from exts.utils.basecog import BaseCog
from exts.utils import errors, permutil

class Events(BaseCog):
    def __init__(self, client):
        super().__init__(client)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f'로그인: {self.client.user.id}')
        await self.client.change_presence(status=discord.Status.online)
        if self.config['betamode']:  
            self.logger.warning('BETA MODE ENABLED')

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        ignoreexc = [discord.http.NotFound]
        excinfo = sys.exc_info()
        errstr = f'{"".join(traceback.format_tb(excinfo[2]))}{excinfo[0].__name__}: {excinfo[1]}'
        self.errlogger.error('\n========== sERROR ==========\n' + errstr + '\n========== sERREND ==========')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        allerrs = (type(error), type(error.__cause__))
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        origintb = traceback.format_exception(type(error), error, error.__traceback__)
        err = [line.rstrip() for line in tb]
        errstr = '\n'.join(err)
        originerr = err = [line.rstrip() for line in origintb]
        originerrstr = '\n'.join(originerr)
        if hasattr(ctx.command, 'on_error'):
            return
        elif commands.errors.MissingRequiredArgument in allerrs:
            return
        elif isinstance(error, errors.NotRegistered):
            await ctx.send(embed=discord.Embed(title='❗ 등록되지 않은 사용자입니다!', description=f'`{self.prefix}등록` 명령으로 등록해주세요!', color=self.color['error']))
            self.msglog.log(ctx, '[미등록 사용자]')
            return
        elif isinstance(error, errors.NotMaster):
            return
        elif isinstance(error, errors.NoCharOnline):
            await ctx.send(embed=discord.Embed(title='❗ 캐릭터가 선택되지 않았습니다!', description=f'`{self.prefix}캐릭터변경` 명령으로 플레이할 캐릭터를 선택해주세요!', color=self.color['error']))
            self.msglog.log(ctx, '[로그인되지 않음]')
            return
        elif errors.ParamsNotExist in allerrs:
            embed = discord.Embed(title=f'❓ 존재하지 않는 명령 옵션입니다: {", ".join(str(error.__cause__.param))}', description=f'`{self.prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요.', color=self.color['error'], timestamp=datetime.datetime.utcnow())
            await ctx.send(embed=embed)
            self.msglog.log(ctx, '[존재하지 않는 명령 옵션]')
            return
        elif isinstance(error, commands.errors.CommandNotFound):
            # embed = discord.Embed(title='❓ 존재하지 않는 명령어입니다!', description=f'`{self.prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요.', color=self.color['error'], timestamp=datetime.datetime.utcnow())
            # await ctx.send(embed=embed)
            # self.msglog.log(ctx, '[존재하지 않는 명령]')
            return
        elif isinstance(error, errors.SentByBotUser):
            return
        elif isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(title='⛔ 길드 전용 명령어', description='이 명령어는 길드 채널에서만 사용할 수 있습니다!', color=self.color['error'], timestamp=datetime.datetime.utcnow())
            await ctx.send(embed=embed)
            self.msglog.log(ctx, '[길드 전용 명령]')
            return
        elif isinstance(error, commands.PrivateMessageOnly):
            embed = discord.Embed(title='⛔ DM 전용 명령어', description='이 명령어는 개인 메시지에서만 사용할 수 있습니다!', color=self.color['error'], timestamp=datetime.datetime.utcnow())
            await ctx.send(embed=embed)
            self.msglog.log(ctx, '[DM 전용 명령]')
            return
        elif isinstance(error, (commands.CheckFailure, commands.MissingPermissions)):
            perms = [permutil.format_perm_by_name(perm) for perm in error.missing_perms]
            embed = discord.Embed(title='⛔ 멤버 권한 부족!', description=f'{ctx.author.mention}, 이 명령어를 사용하려면 다음과 같은 길드 권한이 필요합니다!\n` ' + '`, `'.join(perms) + '`', color=self.color['error'], timestamp=datetime.datetime.utcnow())
            await ctx.send(embed=embed)
            self.msglog.log(ctx, '[멤버 권한 부족]')
            return
        elif isinstance(error.__cause__, discord.HTTPException):
            if error.__cause__.code == 50013:
                missings = permutil.find_missing_perms_by_tbstr(originerrstr)
                fmtperms = [permutil.format_perm_by_name(perm) for perm in missings]
                embed = discord.Embed(title='⛔ 봇 권한 부족!', description='이 명령어를 사용하는 데 필요한 봇의 권한이 부족합니다!\n`' + '`, `'.join(fmtperms) + '`', color=self.color['error'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[봇 권한 부족]')
                return
            elif error.__cause__.code == 50035:
                embed = discord.Embed(title='❗ 메시지 전송 실패', description='보내려고 하는 메시지가 너무 길어 전송에 실패했습니다.', color=self.color['error'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[너무 긴 메시지 전송 시도]')
                return
            else:
                await ctx.send('오류 코드: ' + str(error.__cause__.code))
        
        if self.cur.execute('select * from userdata where id=%s and type=%s', (ctx.author.id, 'Master')) == 0:
            self.errlogger.error('\n========== CMDERROR ==========\n' + errstr + '\n========== CMDERREND ==========')
            embed = discord.Embed(title='❌ 오류!', description=f'무언가 오류가 발생했습니다! 오류 메시지:\n```python\n{str(error)}```\n오류 정보가 기록되었습니다. 나중에 개발자가 처리하게 되며 빠른 처리를 위해서는 서포트 서버에 문의하십시오.', color=self.color['error'], timestamp=datetime.datetime.utcnow())
            await ctx.send(embed=embed)
        else:
            print('\n========== CMDERROR ==========\n' + errstr + '\n========== CMDERREND ==========')
            embed = discord.Embed(title='❌ 오류!', description=f'무언가 오류가 발생했습니다!\n```python\n{errstr}```', color=self.color['error'], timestamp=datetime.datetime.utcnow())
            if ctx.channel.type != discord.ChannelType.private:
                await ctx.send(ctx.author.mention, embed=discord.Embed(title='❌ 오류!', description='개발자용 오류 메시지를 DM으로 전송했습니다.', color=self.color['error']))
            try:
                await ctx.author.send('오류 발생 명령어: `' + ctx.message.content + '`', embed=embed)
            except discord.HTTPException as exc:
                if exc.code == 50035:
                    await ctx.author.send(embed=discord.Embed(title='❌ 오류!', description=f'무언가 오류가 발생했습니다. 오류 메시지가 너무 길어 파일로 첨부됩니다.', color=self.color['error']), file=discord.File(fp=io.StringIO(errstr), filename='errcontent.txt'))
            finally:
                self.msglog.log(ctx, '[커맨드 오류]')

def setup(client):
    cog = Events(client)
    client.add_cog(cog)