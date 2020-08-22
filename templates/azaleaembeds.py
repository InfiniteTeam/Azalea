import discord
from discord.ext import commands
import datetime
import re
from utils import pager, timedelta
from utils.basecog import BaseCog
from utils.embedmgr import aEmbedBase, EmbedMgr, aMsgBase
from db import help

#
class SendingHelp(aEmbedBase):
    async def ko(self):
        return discord.Embed(title='{} 도움말을 전송하고 있습니다...'.format(self.cog.emj.get(self.ctx, 'loading')), color=self.cog.color['info'])
    async def en(self):
        return discord.Embed(title='{} Sending help message...'.format(self.cog.emj.get(self.ctx, 'loading')), color=self.cog.color['info'])

#   
class SentHelp(aEmbedBase):
    async def ko(self, msg: discord.Message):
        return discord.Embed(title='{} 도움말을 전송했습니다!'.format(self.cog.emj.get(self.ctx, 'check')), description=f'**[DM 메시지]({msg.jump_url})**를 확인하세요!', color=self.cog.color['success'])
    async def en(self, msg: discord.Message):
        return discord.Embed(title='{} The help message has been sent.'.format(self.cog.emj.get(self.ctx, 'check')), description=f'**Check your [DM]({msg.jump_url})!**', color=self.cog.color['success'])

#
class Help(aEmbedBase):
    async def ko(self):
        embed = discord.Embed(title='📃 Azalea 전체 명령어', description='(소괄호)는 필수 입력, [대괄호]는 선택 입력입니다.\n\n', color=self.cog.color['primary'])
        for name, value in help.gethelps():
            embed.add_field(
                name='🔸' + name,
                value=value.format(p=self.cog.prefix),
                inline=False
            )
        return embed
    async def en(self):
        embed = discord.Embed(title='📃 Azalea All Commands', description='(Round brackets) are required, [Square brackets] are optional.\n\n', color=self.cog.color['primary'])
        for name, value in help.gethelps():
            embed.add_field(
                name='🔸' + name,
                value=value.format(p=self.cog.prefix),
                inline=False
            )
        return embed
    
#
class Info(aEmbedBase):
    async def ko(self):
        uptimenow = re.findall(r'\d+', str(datetime.datetime.now() - self.cog.client.get_data('start')))
        uptimestr = ''
        if len(uptimenow) == 4:
            if int(uptimenow[0]) > 0:
                uptimestr += f'{int(uptimenow[0])}시간 '
            if int(uptimenow[1]) > 0:
                uptimestr += f'{int(uptimenow[1])}분 '
            if int(uptimenow[2]) > 0:
                uptimestr += f'{int(uptimenow[2])}초 '
        if len(uptimenow) == 5:
            if int(uptimenow[0]) > 0:
                uptimestr += f'{int(uptimenow[0])}일 '
            if int(uptimenow[1]) > 0:
                uptimestr += f'{int(uptimenow[1])}시간 '
            if int(uptimenow[2]) > 0:
                uptimestr += f'{int(uptimenow[2])}분 '
            if int(uptimenow[3]) > 0:
                uptimestr += f'{int(uptimenow[3])}초 '
                
        return discord.Embed(title='🏷 Azalea 정보', description=f'Azalea 버전: {self.cog.client.get_data("version_str")}\n실행 시간: {uptimestr}\nDiscord.py 버전: {discord.__version__}', color=self.cog.color['primary'])
    
    async def en(self):
        uptimenow = re.findall(r'\d+', str(datetime.datetime.now() - self.cog.client.get_data('start')))
        uptimestr = ''
        if len(uptimenow) == 4:
            if int(uptimenow[0]) > 0:
                uptimestr += f'{int(uptimenow[0])} Hours '
            if int(uptimenow[1]) > 0:
                uptimestr += f'{int(uptimenow[1])} Minutes '
            if int(uptimenow[2]) > 0:
                uptimestr += f'{int(uptimenow[2])} Seconds '
        if len(uptimenow) == 5:
            if int(uptimenow[0]) > 0:
                uptimestr += f'{int(uptimenow[0])} Days '
            if int(uptimenow[1]) > 0:
                uptimestr += f'{int(uptimenow[1])} Hours '
            if int(uptimenow[2]) > 0:
                uptimestr += f'{int(uptimenow[2])} Minutes '
            if int(uptimenow[3]) > 0:
                uptimestr += f'{int(uptimenow[3])} Seconds '
                
        return discord.Embed(title='🏷 Azalea Information', description=f'Azalea Version: {self.cog.client.get_data("version_str")}\nRunning Time: {uptimestr}\nDiscord.py Version: {discord.__version__}', color=self.cog.color['primary'])

#
class Ping(aEmbedBase):
    async def ko(self, mping):
        embed = discord.Embed(title='🏓 퐁!', color=self.cog.color['primary'])
        embed.add_field(name='Discord 게이트웨이', value=f'{self.cog.client.get_data("ping")[0]}ms')
        embed.add_field(name='메시지 지연시간', value=str(mping))
        pl = self.cog.client.get_data("ping")[1]
        if pl == 0:
            pinglevel = '🔵 매우 좋음'
        elif pl == 1:
            pinglevel = '🟢 양호함'
        elif pl == 2:
            pinglevel = '🟡 보통'
        elif pl == 3:
            pinglevel = '🔴 나쁨'
        elif pl == 4:
            pinglevel = '⚪ 매우나쁨'
        embed.set_footer(text=pinglevel)
        return embed
    
    async def en(self, mping):
        embed = discord.Embed(title='🏓 Pong!', color=self.cog.color['primary'])
        embed.add_field(name='Discord Gateway', value=f'{self.cog.client.get_data("ping")[0]}ms')
        embed.add_field(name='Message Latency', value=str(mping))
        pl = self.cog.client.get_data("ping")[1]
        if pl == 0:
            pinglevel = '🔵 Very good'
        elif pl == 1:
            pinglevel = '🟢 Good'
        elif pl == 2:
            pinglevel = '🟡 Normal'
        elif pl == 3:
            pinglevel = '🔴 Bad'
        elif pl == 4:
            pinglevel = '⚪ Very Bad'
        embed.set_footer(text=pinglevel)
        return embed
 
#
class Shard(aEmbedBase):
    async def ko(self):
        gshs = self.cog.client.get_data("guildshards")
        if gshs:
            return discord.Embed(description=f'**이 서버의 샤드 아이디는 `{self.ctx.guild.shard_id}`입니다.**\n현재 총 {gshs.__len__()} 개의 샤드가 활성 상태입니다.', color=self.cog.color['info'])
        else:
            return discord.Embed(description=f'**현재 Azalea는 자동 샤딩을 사용하고 있지 않습니다.**', color=self.cog.color['info'])
        
    async def en(self):
        gshs = self.cog.client.get_data("guildshards")
        if gshs:
            return discord.Embed(description=f'**The shard id of this server is `{self.ctx.guild.shard_id}`.**\nCurrently, {gshs.__len__()} shards active.', color=self.cog.color['info'])
        else:
            return discord.Embed(description=f"**Currently Azalea doesn't use auto sharding.**", color=self.cog.color['info'])

#
# NOTIFICATION EMBEDS
#
class Notice_base(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title='📢 공지채널 설정',
            description='',
            color=self.cog.color['ask']
        )
    
    async def en(self):
        return discord.Embed(
            title='📢 Notification channel setting',
            description='',
            color=self.cog.color['ask']
        )
    
class Notice_already_this_channel(aEmbedBase):
    async def ko(self):
        embed = discord.Embed(
            title=f'❓ 이미 이 채널이 공지채널로 설정되어 있습니다!',
            description='',
            color=self.cog.color['ask']
        )
        embed.description += '\n공지를 끄려면 ⛔ 로 반응해주세요! 취소하려면 ❌ 로 반응해주세요.'
        return embed
        
    async def en(self):
        embed = discord.Embed(
            title=f'❓ This channel is already set as an announcement channel!',
            description='',
            color=self.cog.color['ask']
        )
        embed.description += '\nReact ⛔ to disable notifications, React ❌ to cancel.'
        return embed
    
class Notice_selection(aEmbedBase):
    async def ko(self, current_notich, mentionchannel, notich):
        embed = await self.cog.embedmgr.get(self.ctx, 'Notice_base')
        embed.description = f'**현재 공지채널은 {current_notich.mention} 로 설정되어 있습니다.**'
        if mentionchannel:
            embed.description += f'\n{notich.mention} 을 공지채널로 설정할까요?'
        else:
            embed.description += '\n현재 채널을 공지채널로 설정할까요?'
        embed.description += '\n공지를 끄려면 ⛔ 로 반응해주세요! 취소하려면 ❌ 로 반응해주세요.'
        return embed
    
    async def en(self, current_notich, mentionchannel, notich):
        embed = await self.cog.embedmgr.get(self.ctx, 'Notice_base')
        embed.description = f'**Currently, the announcement channel is set to {current_notich.mention}.**'
        if mentionchannel:
            embed.description += f'\nDo you want to set {notich.mention} as the announcement channel?'
        else:
            embed.description += f'\nDo you want to set this channel as an announcement channel?'
        embed.description += '\nReact ⛔ to disable notifications, React ❌ to cancel.'
        return embed
    
class Notice_not_selected(aEmbedBase):
    async def ko(self, channel, notich):
        embed = await self.cog.embedmgr.get(self.ctx, 'Notice_base')
        embed.description = f'**이 서버에는 공지채널이 설정되어있지 않아 공지가 꺼져있습니다.**'
        if channel:
            embed.description += f'\n{notich.mention} 을 공지채널로 설정할까요?'
        else:
            embed.description += '\n현재 채널을 공지채널로 설정할까요?'
        return embed
    
    async def en(self, channel, notich):
        embed = await self.cog.embedmgr.get(self.ctx, 'Notice_base')
        embed.description = f'**Notification is disabled on this server.**'
        if channel:
            embed.description += f'\nDo you want to set {notich.mention} as the announcement channel?'
        else:
            embed.description += f'\nDo you want to set this channel as an announcement channel?'
        return embed

class Notice_set_done(aEmbedBase):
    async def ko(self, notich):
        return discord.Embed(
            title=f'{self.cog.emj.get(self.ctx, "check")} 공지 채널을 성공적으로 설정했습니다!',
            description=f'이제 {notich.mention} 채널에 공지를 보냅니다.',
            color=self.cog.color['info']
        )
    
    async def en(self, notich):
        return discord.Embed(
            title=f'{self.cog.emj.get(self.ctx, "check")} The notification channel has been set up successfully!',
            description=f'The announcements will send to {notich.mention}.',
            color=self.cog.color['info']
        )
    
class Notice_turn_off(aEmbedBase):
    async def ko(self):
        return discord.Embed(title='❌ 공지 기능을 껐습니다!', color=self.cog.color['error'])
    async def en(self):
        return discord.Embed(title='❌ Notifications have been disabled! ', color=self.cog.color['error'])
    
#
# REGISTERING EMBEDS
#

class Register_already_registered(aEmbedBase):
    async def ko(self):
        return discord.Embed(title=f'{self.cog.emj.get(self.ctx, "check")} 이미 등록된 사용자입니다!', color=self.cog.color['info'])
    async def en(self):
        return discord.Embed(title=f'{self.cog.emj.get(self.ctx, "check")} You already registered to Azalea.', color=self.cog.color['info'])
    
class  Register(aEmbedBase):
    async def ko(self):
        embed = discord.Embed(title='Azalea 등록', description='**Azalea를 이용하기 위한 이용약관 및 개인정보 취급방침입니다. Azalea를 이용하려면 동의가 필요 합니다.**', color=self.cog.color['ask'])
        embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
        embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
        return embed
    async def en(self):
        embed = discord.Embed(title='Azalea sign up', description='**These are the terms of use and privacy policy for using Azalea. Consent is required to use Azalea.**', color=self.cog.color['ask'])
        embed.add_field(name='ㅤ', value='[Terms of Use](https://www.infiniteteam.me/tos)\n', inline=True)
        embed.add_field(name='ㅤ', value='[Privacy Policy](https://www.infiniteteam.me/privacy)\n', inline=True)
        return embed
    
class Register_done(aEmbedBase):
    async def ko(self):
        return discord.Embed(title=f'등록되었습니다. `{self.cog.prefix}help` 명령으로 전체 명령을 볼 수 있습니다.', color=self.cog.color['success'])
    async def en(self):
        return discord.Embed(title=f'Signed up successfully. Enter `{self.cog.prefix}help` to see all commands.', color=self.cog.color['success'])
    
#
# WITHDRAW 
#

class Withdraw(aEmbedBase):
    async def ko(self):
        embed = discord.Embed(title='Azalea 탈퇴',
        description='''**Azalea 이용약관 및 개인정보 취급방침 동의를 철회하고, Azalea를 탈퇴하게 됩니다.**
        이 경우 _사용자님의 모든 데이터(개인정보 취급방침을 참조하십시오)_가 Azalea에서 삭제되며, __되돌릴 수 없습니다.__
        계속할까요?''', color=self.cog.color['warn'])
        embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
        embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
        return embed
    
class Withdraw_done(aEmbedBase):
    async def ko(self):
        return discord.Embed(title='탈퇴되었습니다.', color=self.cog.color['info'])

class Withdraw_already(aEmbedBase):
    async def ko(self):
        return discord.Embed(title='❌ 이미 탈퇴된 사용자입니다.', color=self.cog.color['error'])
    

#
# NEWS
#

class News(aEmbedBase):
    async def ko(self, pgr: pager.Pager, *, total: int):
        embed = discord.Embed(title='📰 뉴스', description='', color=self.cog.color['info'])
        for one in pgr.get_thispage():
            if one.content:
                if one.content.__len__() > 110:
                    content = '> ' + one.content[:110] + '...\n'
                else:
                    content = '> ' + one.content + '\n'
            else:
                content = ''
            td = datetime.datetime.now() - one.datetime
            if td < datetime.timedelta(minutes=1):
                pubtime = '방금'
            else:
                pubtime = list(timedelta.format_timedelta(td).values())[0] + ' 전'
            embed.description += f'🔹 **`{one.title}`**\n{content}**- {one.company}**, {pubtime}\n\n'
        if total > 40:
            embed.description += '```{}/{} 페이지, 전체 {}건 중 최신 {}건```'.format(pgr.now_pagenum()+1, len(pgr.pages()), total, pgr.objlen())
        else:
            embed.description += '```{}/{} 페이지, 전체 {}건```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
        embed.set_footer(text='* 이 뉴스는 재미 및 게임 플레이를 위한 실제와 상관없는 픽션임을 알려 드립니다.')
        return embed

class News_publish_continue_ask(aMsgBase):
    async def ko(self):
        return f'{self.ctx.author.mention} 다음과 같이 발행할까요?'

class News_publish_continue(aEmbedBase):
    async def ko(self, *, company, title, viewcontent):
        embed = discord.Embed(title='📰 뉴스', color=self.cog.color['info'])
        embed.description = f'🔹 **`{title}`**\n{viewcontent}**- {company}**, 방금'
        embed.set_author(name='뉴스 발행 미리보기')
        return embed