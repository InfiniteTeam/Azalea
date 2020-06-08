import discord
from discord.ext import commands
import datetime
import re
import json
import asyncio
import typing
from exts.utils.basecog import BaseCog

class Azaleacmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            if cmd.name != '등록':
                cmd.add_check(self.check.registered)

    @commands.command(name='도움')
    async def _help(self, ctx: commands.Context):
        embed = discord.Embed(title='📃 Azalea 전체 명령어', description='(소괄호)는 필수 입력, [대괄호]는 선택 입력입니다.\n\n', color=self.color['primary'])
        embed.add_field(
            name='기본 명령어',
            value=
            """\
            `{p}도움`: 도움말 메시지를 표시합니다.
            `{p}정보`: 봇 정보를 확인합니다.
            `{p}핑`: 봇 정보를 확인합니다.
            `{p}샤드`: 현재 서버의 Azalea 샤드 번호를 확인합니다.
            `{p}공지채널 [#채널멘션]`: Azalea 공지를 받을 채널을 설정합니다.
            """.format(p=self.prefix)
        )
        await ctx.send(embed=embed)
        if ctx.channel.type != discord.ChannelType.private:
            await ctx.send(embed=discord.Embed(title='{} DM으로 도움말을 전송했습니다!'.format(self.emj.get(ctx, 'check')), description='DM을 확인하세요!', color=self.color['success']))
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

        embed=discord.Embed(title='🏷 Azalea 정보', description=f'Azalea 버전: {self.client.get_data("version_str")}\n실행 시간: {uptimestr}\nDiscord.py 버전: {discord.__version__}', color=self.color['primary'])
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[정보]')

    @commands.command(name='핑', aliases=['지연시간', '레이턴시'])
    async def _ping(self, ctx: commands.Context):
        embed=discord.Embed(title='🏓 퐁!', description=f'**디스코드 지연시간: **{self.client.get_data("ping")[0]}ms - {self.client.get_data("ping")[1]}\n\n디스코드 지연시간은 디스코드 웹소켓 프로토콜의 지연 시간(latency)을 뜻합니다.', color=self.color['primary'])
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[핑]')

    @commands.command(name='샤드')
    async def _shard_id(self, ctx: commands.Context):
        await ctx.send(embed=discord.Embed(description=f'**이 서버의 샤드 아이디는 `{ctx.guild.shard_id}`입니다.**\n현재 총 {self.client.get_data("guildshards").__len__()} 개의 샤드가 활성 상태입니다.', color=self.color['info']))
        self.msglog.log(ctx, '[샤드]')

    @commands.command(name='공지채널')
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def _notice(self, ctx: commands.Context, *, channel: typing.Optional[discord.TextChannel]=None):
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
        self.cur.execute('select * from serverdata where id=%s', ctx.guild.id)
        ch = ctx.guild.get_channel(self.cur.fetchone()['noticechannel'])
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
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in notiemjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=20, check=notich_check)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
            self.msglog.log(ctx, '[공지채널: 시간 초과]')
        else:
            em = str(reaction.emoji)
            if em == '⭕':
                self.cur.execute('update serverdata set noticechannel=%s where id=%s', (notich.id, ctx.guild.id))
                await ctx.send(embed=discord.Embed(title=f'{self.emj.get(ctx, "check")} 공지 채널을 성공적으로 설정했습니다!', description=f'이제 {notich.mention} 채널에 공지를 보냅니다.', color=self.color['info']))
                self.msglog.log(ctx, '[공지채널: 설정 완료]')
            elif em == '❌':
                await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[공지채널: 취소됨]')
            elif em == '⛔':
                self.cur.execute('update serverdata set noticechannel=%s where id=%s', (None, ctx.guild.id))
                await ctx.send(embed=discord.Embed(title=f'❌ 공지 기능을 껐습니다!', color=self.color['error']))
                self.msglog.log(ctx, '[공지채널: 비활성화]')


    @commands.command(name='등록')
    async def _register(self, ctx: commands.Context):
        if self.cur.execute('select * from userdata where id=%s', ctx.author.id) != 0:
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
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=20.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
            self.msglog.log(ctx, '[등록: 시간 초과]')
        else:
            remj = str(reaction.emoji)
            if remj == '⭕':
                if self.cur.execute('select * from userdata where id=%s', ctx.author.id) == 0:
                    now = datetime.datetime.now()
                    baseitem = json.dumps(self.templates['baseitem'], ensure_ascii=False)
                    if self.cur.execute('insert into userdata(id, level, type) values (%s, %s, %s)', (ctx.author.id, 1, 'User')) == 1:
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
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=20.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
            self.msglog.log(ctx, '[탈퇴: 시간 초과]')
        else:
            remj = str(reaction.emoji)
            if remj == '⭕':
                if self.cur.execute('select * from userdata where id=%s', (ctx.author.id)):
                    if self.cur.execute('delete from userdata where id=%s', ctx.author.id):
                        await ctx.send('탈퇴되었습니다.')
                        self.msglog.log(ctx, '[탈퇴: 완료]')
                else:
                    await ctx.send('이미 탈퇴된 사용자입니다.')
                    self.msglog.log(ctx, '[탈퇴: 이미 탈퇴됨]')
            elif remj == '❌':
                await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[탈퇴: 취소됨]')

def setup(client):
    cog = Azaleacmds(client)
    client.add_cog(cog)