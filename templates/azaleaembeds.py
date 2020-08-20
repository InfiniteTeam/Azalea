import discord
from discord.ext import commands
import datetime
import re
from utils import pager, timedelta
from utils.basecog import BaseCog
from utils.embedmgr import aEmbedBase
from db import help

class SendingHelp(aEmbedBase):
    async def ko(self):
        return discord.Embed(title='{} 도움말을 전송하고 있습니다...'.format(self.cog.emj.get(self.ctx, 'loading')), color=self.cog.color['info'])
    async def en(self):
        return discord.Embed(title='{} Sending help message...'.format(self.cog.emj.get(self.ctx, 'loading')), color=self.cog.color['info'])
    
class SentHelp(aEmbedBase):
    async def ko(self, msg: discord.Message):
        return discord.Embed(title='{} 도움말을 전송했습니다!'.format(self.cog.emj.get(self.ctx, 'check')), description=f'**[DM 메시지]({msg.jump_url})**를 확인하세요!', color=self.cog.color['success'])
    async def en(self, msg: discord.Message):
        return discord.Embed(title='{} The help message has been sent.'.format(self.cog.emj.get(self.ctx, 'check')), description=f'**Check your [DM]({msg.jump_url})!**', color=self.cog.color['success'])

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

async def news_embed(cog: BaseCog, pgr: pager.Pager, *, total: int):
    embed = discord.Embed(title='📰 뉴스', description='', color=cog.color['info'])
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