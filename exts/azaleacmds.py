import discord
from discord.ext import commands
import datetime
import re
import asyncio
from exts.utils.basecog import BaseCog

class Azaleacmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            if cmd.name != '등록':
                cmd.add_check(self.check.registered)
            if cmd.name == '공지채널':
                cmd.add_check(commands.guild_only)

    @commands.command(name='도움')
    async def _help(self, ctx: commands.Context):
        embed = discord.Embed(title='📃 Azalea 전체 명령어', description='**[전체 명령어 보기](https://help.infiniteteam.me/azaleabot)**', color=self.color['primary'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[도움]')

    @commands.command(name='정보')
    async def _info(self, ctx: commands.Context):
        uptimenow = re.findall('\d+', str(datetime.datetime.now() - self.client.get_data('start')))
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

        embed=discord.Embed(title='🏷 Azalea 정보', description=f'Azalea 버전: {self.client.get_data("version_str")}\n실행 시간: {uptimestr}\nDiscord.py 버전: {discord.__version__}', color=self.color['primary'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[정보]')

    @commands.command(name='핑')
    async def _ping(self, ctx: commands.Context):
        embed=discord.Embed(title='🏓 퐁!', description=f'**디스코드 지연시간: **{self.client.get_data("ping")[0]}ms - {self.client.get_data("ping")[1]}\n\n디스코드 지연시간은 디스코드 웹소켓 프로토콜의 지연 시간(latency)을 뜻합니다.', color=self.color['primary'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[핑]')

    @commands.command(name='샤드')
    async def _shard_id(self, ctx: commands.Context):
        await ctx.send(embed=discord.Embed(description=f'**이 서버의 샤드 아이디는 `{ctx.guild.shard_id}`입니다.**\n현재 총 {self.client.get_data("guildshards").__len__()} 개의 샤드가 활성 상태입니다.', color=self.color['info'], timestamp=datetime.datetime.utcnow()))
        self.msglog.log(ctx, '[샤드]')

    @commands.command(name='공지채널')
    @commands.has_guild_permissions(administrator=True)
    async def _notice(self, ctx: commands.Context, *mention):
        mention = ctx.message.channel_mentions
        if mention:
            notich = mention[0]
        else:
            notich = ctx.channel
        current_id = self.cur.execute('select * from serverdata where id=%s', ctx.guild.id)
        if current_id:
            ch = ctx.guild.get_channel(self.cur.fetchone()['noticechannel'])
            if notich == ch:
                await ctx.send(embed=discord.Embed(title=f'❓ 이미 이 채널이 공지채널로 설정되어 있습니다!', color=self.color['error']))
                self.msglog.log(ctx, '[공지채널: 이미 설정된 채널]')
            elif ch:
                if mention:
                    embed = discord.Embed(title='📢 공지채널 설정', description=f'**현재 공지채널은 {ch.mention} 로 설정되어 있습니다.**\n{notich.mention} 을 공지채널로 설정할까요?\n20초 안에 선택해주세요.', color=self.color['ask'], timestamp=datetime.datetime.utcnow())
                else:
                    embed = discord.Embed(title='📢 공지채널 설정', description=f'**현재 공지채널은 {ch.mention} 로 설정되어 있습니다.**\n현재 채널을 공지채널로 설정할까요?\n20초 안에 선택해주세요.', color=self.color['ask'], timestamp=datetime.datetime.utcnow())
                msg = await ctx.send(embed=embed)
                self.msglog.log(ctx, '[공지채널: 공지채널 설정]')
                for rct in ['⭕', '❌']:
                    await msg.add_reaction(rct)
                def notich_check(reaction, user):
                    return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in ['⭕', '❌']
                try:
                    reaction, user = await self.client.wait_for('reaction_add', timeout=20, check=notich_check)
                except asyncio.TimeoutError:
                    await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
                    self.msglog.log(ctx, '[공지채널: 시간 초과]')
                else:
                    em = str(reaction.emoji)
                    if em == '⭕':
                        self.cur.execute('update serverdata set noticechannel=%s where id=%s', (notich.id, ctx.guild.id))
                        await ctx.send(embed=discord.Embed(title=f'{self.emj.get(ctx, "check")} 공지 채널을 성공적으로 설정했습니다!', description=f'이제 {notich.mention} 채널에 공지를 보냅니다.', color=self.color['info'], timestamp=datetime.datetime.utcnow()))
                        self.msglog.log(ctx, '[공지채널: 설정 완료]')
                    elif em == '❌':
                        await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
                        self.msglog.log(ctx, '[공지채널: 취소됨]')

    @commands.command(name='등록')
    async def _register(self, ctx: commands.Context):
        if self.cur.execute('select * from userdata where id=%s', ctx.author.id):
            await ctx.send(embed=discord.Embed(title=f'{self.emj.get(ctx, "check")} 이미 등록된 사용자입니다!', color=self.color['info']))
            self.msglog.log(ctx, '[등록: 이미 등록됨]')
        else:
            embed = discord.Embed(title='Azalea 등록', description='**Azalea을 이용하기 위한 이용약관 및 개인정보 취급방침입니다. 동의하시면 20초 안에 `동의`를 입력해주세요.**', color=self.color['ask'], timestamp=datetime.datetime.utcnow())
            embed.add_field(name='ㅤ', value='[이용약관](https://www.infiniteteam.me/tos)\n', inline=True)
            embed.add_field(name='ㅤ', value='[개인정보 취급방침](https://www.infiniteteam.me/privacy)\n', inline=True)
            await ctx.send(content=ctx.author.mention, embed=embed)
            self.msglog.log(ctx, '[등록: 등록하기]')
            def checkmsg(m):
                return m.channel == ctx.channel and m.author == ctx.author and m.content == '동의'
            try:
                msg = await self.client.wait_for('message', timeout=20.0, check=checkmsg)
            except asyncio.TimeoutError:
                await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
                self.msglog.log(ctx, '[등록: 시간 초과]')
            else:
                if self.cur.execute('select * from userdata where id=%s', (msg.author.id)) == 0:
                    now = datetime.datetime.now()
                    if self.cur.execute('insert into userdata(id, level, type, date) values (%s, %s, %s, %s)', (msg.author.id, 1, 'User', datetime.date(now.year, now.month, now.day))) == 1:
                        await ctx.send(f'등록되었습니다. `{self.client.command_prefix}도움` 명령으로 전체 명령을 볼 수 있습니다.')
                        self.msglog.log(ctx, '[등록: 완료]')
                else:
                    await ctx.send('이미 등록된 사용자입니다.')
                    self.msglog.log(ctx, '[등록: 이미 등록됨]')

def setup(client):
    cog = Azaleacmds(client)
    client.add_cog(cog)