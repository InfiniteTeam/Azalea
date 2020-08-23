import discord
from discord.ext import commands
import traceback
import datetime
import asyncio
import io
import math
import sys
import aiomysql
from utils.basecog import BaseCog
from utils import errors, permutil, datamgr, progressbar
import uuid
from configs import advlogging

class Events(BaseCog):
    def __init__(self, client):
        super().__init__(client)

    @commands.Cog.listener()
    async def on_levelup(self, charuuid, before, after, channel_id):
        cmgr = datamgr.CharMgr(self.pool)
        char = await cmgr.get_character(charuuid)
        user = self.client.get_user(char.id)
        sdgr = datamgr.SettingDBMgr(self.datadb)
        smgr = datamgr.SettingMgr(self.pool, sdgr, charuuid)
        samgr = datamgr.StatMgr(self.pool, char.uid)
        edgr = datamgr.ExpTableDBMgr(self.datadb)
        level = await samgr.get_level(edgr)
        nowexp = char.stat.EXP
        req = edgr.get_required_exp(level+1)
        accu = edgr.get_accumulate_exp(level+1)
        prev_req = edgr.get_required_exp(level)
        prev_accu = edgr.get_accumulate_exp(level)
        if req-prev_req <= 0:
            percent = 0
        else:
            percent = math.trunc((req-accu+nowexp)/req*1000)/10

        embed = discord.Embed(title=f'🆙 `{char.name}` 의 레벨이 올랐습니다!', description='레벨이 **`{}`** 에서 **`{}`** (으)로 올랐습니다!'.format(before, after), color=self.color['info'])
        embed.add_field(name='• 현재 경험치', value='>>> {}ㅤ **{}/{}** ({}%)\n레벨업 필요 경험치: **`{}`/`{}`**'.format(
            progressbar.get(None, self.emj, req-accu+nowexp, req, 10),
            format(req-accu+nowexp, ','), format(req, ','), percent, nowexp, accu
        ))
        embed.set_footer(text="자세한 정보는 '{}캐릭터 정보' 를 입력해 확인하세요!".format(self.prefix))
        whereset = await smgr.get_setting('where-to-levelup-msg')
        if channel_id is None or whereset == 'dm':
            await user.send(embed=embed)
        elif whereset == 'current':
            await self.client.get_channel(channel_id).send(user.mention, embed=embed)

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
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                uid = uuid.uuid4()
                allerrs = (type(error), type(error.__cause__))
                tb = traceback.format_exception(type(error), error, error.__traceback__)
                origintb = traceback.format_exception(type(error), error, error.__traceback__)
                err = [line.rstrip() for line in tb]
                errstr = '\n'.join(err)
                originerr = err = [line.rstrip() for line in origintb]
                originerrstr = '\n'.join(originerr)
                if isinstance(error, errors.MissingRequiredArgument):
                    await ctx.send(embed=discord.Embed(title='❗ 명령어에 빠진 부분이 있습니다!', description=f'**`{error.paramdesc}`이(가) 필요합니다!**\n자세한 명령어 사용법은 `{self.prefix}도움` 을 통해 확인하세요!', color=self.color['error']))
                    self.msglog.log(ctx, f'[필요한 명령 인자 없음: "{error.param.name}"({error.paramdesc})]')
                    return
                elif isinstance(error, discord.NotFound):
                    self.msglog.log(ctx, f'[찾을 수 없음]')
                    return
                elif isinstance(error, commands.CommandOnCooldown):
                    """
                    cooldown = timedelta.format_timedelta(datetime.timedelta(seconds=error.retry_after))
                    cdstr = ' '.join(cooldown.values())
                    await ctx.send(embed=discord.Embed(title='⏱ 쿨타임 중입니다!', description='{} 후에 다시 할수 있어요.'.format(cdstr), color=self.color['info']))
                    self.msglog.log(ctx, f'[쿨다운 중]')
                    """
                    return
                elif commands.errors.MissingRequiredArgument in allerrs:
                    self.msglog.log(ctx, '[필요한 명령 인자 없음]')
                    return
                elif isinstance(error, errors.NotRegistered):
                    await ctx.send(embed=discord.Embed(title='❗ 등록되지 않은 사용자입니다!', description=f'`{self.prefix}등록` 명령으로 등록해주세요!', color=self.color['error']))
                    self.msglog.log(ctx, '[미등록 사용자]')
                    return
                elif isinstance(error, errors.NotMaster):
                    return
                elif isinstance(error, errors.onInspection):
                    await ctx.send(embed=discord.Embed(title='❗ 현재 Azalea는 점검 중입니다.', description=f'점검 중에는 운영자만 사용할 수 있습니다.', color=self.color['error']))
                    self.msglog.log(ctx, '[점검중]')
                    return
                elif isinstance(error, errors.NoCharOnline):
                    await ctx.send(embed=discord.Embed(title='❗ 캐릭터가 선택되지 않았습니다!', description=f'`{self.prefix}캐릭터 변경` 명령으로 플레이할 캐릭터를 선택해주세요!', color=self.color['error']))
                    self.msglog.log(ctx, '[로그인되지 않음]')
                    return
                elif errors.ParamsNotExist in allerrs:
                    embed = discord.Embed(title=f'❓ 존재하지 않는 명령 옵션입니다: {", ".join(str(error.__cause__.param))}', description=f'`{self.prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요.', color=self.color['error'])
                    await ctx.send(embed=embed)
                    self.msglog.log(ctx, '[존재하지 않는 명령 옵션]')
                    return
                elif isinstance(error, commands.CommandNotFound):
                    """
                    embed = discord.Embed(title='❓ 존재하지 않는 명령어입니다!', description=f'`{self.prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요.', color=self.color['error'])
                    embed.set_image(url='https://mblogthumb-phinf.pstatic.net/20110323_149/yean5rang_1300858060958TRSBY_JPEG/%B1%D7%B7%B1%B0%C7_%BE%F8%B4%D9.jpg?type=w2')
                    await ctx.send(embed=embed)
                    self.msglog.log(ctx, '[존재하지 않는 명령]')
                    """
                    return
                elif isinstance(error, errors.SentByBotUser):
                    return
                elif isinstance(error, commands.NoPrivateMessage):
                    embed = discord.Embed(title='⛔ 길드 전용 명령어', description='이 명령어는 길드 채널에서만 사용할 수 있습니다!', color=self.color['error'])
                    await ctx.send(embed=embed)
                    self.msglog.log(ctx, '[길드 전용 명령]')
                    return
                elif isinstance(error, commands.PrivateMessageOnly):
                    embed = discord.Embed(title='⛔ DM 전용 명령어', description='이 명령어는 개인 메시지에서만 사용할 수 있습니다!', color=self.color['error'])
                    await ctx.send(embed=embed)
                    self.msglog.log(ctx, '[DM 전용 명령]')
                    return
                elif isinstance(error, commands.MissingPermissions):
                    perms = [permutil.format_perm_by_name(perm) for perm in error.missing_perms]
                    embed = discord.Embed(title='⛔ 멤버 권한 부족!', description=f'{ctx.author.mention}, 이 명령어를 사용하려면 다음과 같은 길드 권한이 필요합니다!\n> **`' + '`, `'.join(perms) + '`**', color=self.color['error'])
                    await ctx.send(embed=embed)
                    self.msglog.log(ctx, '[멤버 권한 부족]')
                    return
                elif isinstance(error, errors.MissingAzaleaPermissions):
                    perms = error.missing_perms
                    embed = discord.Embed(title='⛔ Azalea 권한 부족!', description=f'{ctx.author.mention}, 이 명령어를 사용하려면 다음과 같은 Azalea 권한이 필요합니다!\n> **`' + '`, `'.join(perms) + '`**', color=self.color['error'])
                    await ctx.send(embed=embed)
                    self.msglog.log(ctx, '[Azalea 권한 부족]')
                    return
                elif isinstance(error.__cause__, discord.HTTPException):
                    if error.__cause__.code == 50013:
                        missings = permutil.find_missing_perms_by_tbstr(originerrstr)
                        fmtperms = [permutil.format_perm_by_name(perm) for perm in missings]
                        if missings:
                            embed = discord.Embed(title='⛔ 봇 권한 부족!', description='이 명령어를 사용하는 데 필요한 봇의 권한이 부족합니다!\n`' + '`, `'.join(fmtperms) + '`', color=self.color['error'])
                        else:
                            embed = discord.Embed(title='⛔ 봇 권한 부족!', description='이 명령어를 사용하는 데 필요한 봇의 권한이 부족합니다!\n부족한 권한이 무엇인지 감지하는 데 실패했습니다. [InfiniteTEAM 서포트 서버]({})로 문의하면 빠르게 도와드립니다.'.format(self.config['support_url']), color=self.color['error'])
                        try:
                            await ctx.send(embed=embed)
                        except discord.Forbidden:
                            self.msglog.log(ctx, '[봇 메시지 전송 권한 없음]')
                        else:
                            self.msglog.print('')
                            self.msglog.log(ctx, '[봇 권한 부족]')
                        return
                    elif error.__cause__.code == 50035:
                        embed = discord.Embed(title='❗ 메시지 전송 실패', description='보내려고 하는 메시지가 너무 길어 전송에 실패했습니다.', color=self.color['error'])
                        await ctx.send(embed=embed)
                        self.msglog.log(ctx, '[너무 긴 메시지 전송 시도]')
                        return
                    elif error.__cause__.code == 50007:
                        embed = discord.Embed(title='❗ 메시지 전송 실패', description='DM(개인 메시지)으로 메시지를 전송하려 했으나 실패했습니다.\n혹시 DM이 비활성화 되어 있지 않은지 확인해주세요!', color=self.color['error'])
                        await ctx.send(ctx.author.mention, embed=embed)
                        self.msglog.log(ctx, '[DM 전송 실패]')
                        return
                    elif error.__cause__.code == 10008:
                        self.msglog.log(ctx, '[찾을 수 없음]')
                        return
                    else:
                        await ctx.send('오류 코드: ' + str(error.__cause__.code))
                
                self.msglog.log(ctx, '[커맨드 오류: {}]'.format(uid))
                await cur.execute('insert into error (uuid, content, datetime) values (%s, %s, %s)', (uid.hex, errstr, datetime.datetime.now()))

                if await cur.execute('select * from userdata where id=%s and type=%s', (ctx.author.id, 'Master')) == 0:
                    self.errlogger.error(f'\n========== CMDERROR ========== {uid.hex}\n' + errstr + '\n========== CMDERREND ==========')
                    embed = discord.Embed(title='❌ 오류!', description=f'무언가 오류가 발생했습니다! 오류 코드:\n```{uid.hex}```\n', color=self.color['error'])
                    embed.set_footer(text='오류 정보가 기록되었습니다. 나중에 개발자가 처리하게 되며 빠른 처리를 위해서는 [InfiniteTEAM 서포트 서버]({})에 문의하십시오.'.format(self.config['support_url']))
                    await ctx.send(embed=embed)

                    async def send_log(channel_id: int):
                        channel = self.client.get_channel(channel_id)
                        if not channel:
                            return
                        try:
                            await channel.send('오류 발생 명령어: `' + ctx.message.content + '`', embed=embed)
                        except discord.HTTPException as exc:
                            if exc.code == 50035:
                                await channel.send(embed=discord.Embed(title='❌ 오류!', description=f'오류 ID: `{uid}`\n무언가 오류가 발생했습니다. 오류 메시지가 너무 길어 파일로 첨부됩니다.', color=self.color['error']), file=discord.File(fp=io.StringIO(errstr), filename='errcontent.txt'))

                    sendlist = []
                    for one in advlogging.ERROR_LOG_CHANNEL_IDS:
                        sendlist.append(send_log(one))
                    await asyncio.gather(*sendlist)
                    
                else:
                    print(f'\n========== CMDERROR ========== {uid.hex}\n' + errstr + '\n========== CMDERREND ==========')
                    embed = discord.Embed(title='❌ 오류!', description=f'무언가 오류가 발생했습니다!\n```{uid.hex}```\n```python\n{errstr}```', color=self.color['error'])
                    try:
                        msg = await ctx.author.send('오류 발생 명령어: `' + ctx.message.content + '`', embed=embed)
                    except discord.HTTPException as exc:
                        if exc.code == 50035:
                            msg = await ctx.author.send(embed=discord.Embed(title='❌ 오류!', description=f'무언가 오류가 발생했습니다. 오류 메시지가 너무 길어 파일로 첨부됩니다.', color=self.color['error']), file=discord.File(fp=io.StringIO(errstr), filename='errcontent.txt'))

                    if ctx.channel.type != discord.ChannelType.private:
                        await ctx.send(ctx.author.mention, embed=discord.Embed(title='❌ 오류!', description=f'개발자용 오류 메시지를 [DM]({msg.jump_url})으로 전송했습니다.', color=self.color['error']))

def setup(client):
    cog = Events(client)
    client.add_cog(cog)