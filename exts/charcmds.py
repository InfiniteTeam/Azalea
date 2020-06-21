import discord
from discord.ext import commands
from exts.utils.basecog import BaseCog
import typing
import datetime
from dateutil.relativedelta import relativedelta
import asyncio
import re
from exts.utils import pager, emojibuttons, timedelta
from exts.utils.datamgr import CharMgr, CharacterType
from templates import ingameembeds, errembeds

class Charcmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            if cmd.name not in ['캐릭터', '캐생', '로그이웃', '캐삭']:
                cmd.add_check(self.check.char_online)

    @commands.group(name='캐릭터', aliases=['캐'], invoke_without_command=True)
    async def _char(self, ctx: commands.Context, *, user: typing.Optional[discord.Member]=None):
        if not user:
            user = ctx.author
        perpage = 5
        cmgr = CharMgr(self.cur)
        chars = cmgr.get_chars(user.id)
        if not chars:
            if ctx.author.id == user.id:
                await ctx.send(embed=discord.Embed(
                    title='🎲 캐릭터가 하나도 없네요!',
                    description='`{}생성` 명령으로 캐릭터를 생성해서 게임을 시작하세요!'.format(self.prefix),
                    color=self.color['warn']
                ))
            else:
                await ctx.send(embed=discord.Embed(
                    title=f'🎲 `{user.name}` 님은 캐릭터가 하나도 없네요!',
                    color=self.color['warn']
                ))
            return
        pgr = pager.Pager(chars, perpage)
        msg = await ctx.send(embed=await ingameembeds.char_embed(user.name, pgr, color=self.color['info']))
        self.msglog.log(ctx, '[캐릭터 목록]')
        if len(pgr.pages()) <= 1:
            return
        for emj in emojibuttons.PageButton.emojis:
            await msg.add_reaction(emj)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emojibuttons.PageButton.emojis
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
                        msg.edit(embed=await ingameembeds.char_embed(user.name, pgr, color=self.color['info'])),
                    )

    @_char.command(name='생성')
    async def _char_create(self, ctx:commands.Context):
        cmgr = CharMgr(self.cur)
        charcount = len(cmgr.get_chars(ctx.author.id))
        if charcount >= self.config['max_charcount']:
            await ctx.send(embed=discord.Embed(title='❌ 캐릭터 슬롯이 모두 찼습니다.', description='유저당 최대 캐릭터 수는 {}개 입니다.'.format(self.config['max_charcount']), color=self.color['error']))
            self.msglog.log(ctx, '[캐릭터 슬롯 부족]')
            return
        namemsg = await ctx.send(embed=discord.Embed(title='🏷 캐릭터 생성 - 이름', description='새 캐릭터를 생성합니다. 캐릭터의 이름을 입력하세요.\n취소하려면 `취소` 를 입력하세요!', color=self.color['ask']))
        self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기]')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content
        try:
            m = await self.client.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            embed = discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info'])
            embed.set_footer(text='이 메시지는 7초 후에 삭제됩니다.')
            await ctx.send(embed=embed, delete_after=7)
            self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 시간 초과]')
        else:
            if m.content == '취소':
                await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 취소됨]')
                return
            elif not (2 <= len(m.content) <= 10):
                await ctx.send(embed=discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='캐릭터 이름은 2글자 이상이여야 합니다.\n다시 시도해 주세요!', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 너무 짧은 이름]')
                return
            elif not re.match('^[ |가-힣|a-z|A-Z|0-9]+$', m.content):
                await ctx.send(embed=discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='캐릭터 이름은 반드시 한글, 영어, 숫자만을 사용해야 합니다.\n다시 시도해 주세요!', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 올바르지 않은 이름]')
                return
            elif self.cur.execute('select * from chardata where name=%s', m.content) != 0:
                await ctx.send(embed=discord.Embed(title='❌ 이미 사용중인 이름입니다!', description='다시 시도해 주세요!', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 이미 사용중인 이름]')
                return
            else:
                for pfx in self.client.command_prefix:
                    if pfx.rstrip().lower() in m.content.lower():
                        await ctx.send(embed=discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='아젤리아 봇 접두사는 이름에 포함할 수 없습니다.\n다시 시도해 주세요!', color=self.color['error']))
                        self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 접두사 포함 금지]')
                        return
                charname = m.content
        typemsg = await ctx.send(embed=discord.Embed(title='🏷 캐릭터 생성 - 직업', color=self.color['ask'],
            description="""\
                `{}` 의 직업을 선택합니다.
                ⚔: 전사
                🏹: 궁수
                🔯: 마법사

                ❌: 취소
            """.format(charname)
        ))
        emjs = ['⚔', '🏹', '🔯', '❌']
        for em in emjs:
            await typemsg.add_reaction(em)
        def rcheck(reaction, user):
            return user == ctx.author and typemsg.id == reaction.message.id and str(reaction.emoji) in emjs
        self.msglog.log(ctx, '[캐릭터 생성: 직업 선택]')
        try:
            reaction, user = await self.client.wait_for('reaction_add', check=rcheck, timeout=20)
        except asyncio.TimeoutError:
            embed = discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info'])
            embed.set_footer(text='이 메시지는 7초 후에 삭제됩니다.')
            await ctx.send(embed=embed, delete_after=7)
            self.msglog.log(ctx, '[캐릭터 생성: 직업 선택: 시간 초과]')
        else:
            e = str(reaction.emoji)
            if e == '❌':
                await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 직업 선택: 취소됨]')
                return
            elif e == '⚔':
                chartype = CharacterType.Knight.name
            elif e == '🏹':
                chartype = CharacterType.Archer.name
            elif e == '🔯':
                chartype = CharacterType.Wizard.name
            
            charcount = len(cmgr.get_chars(ctx.author.id))
            if charcount >= self.config['max_charcount']:
                await ctx.send(embed=discord.Embed(title='❌ 캐릭터 슬롯이 모두 찼습니다.', description='유저당 최대 캐릭터 수는 {}개 입니다.'.format(self.config['max_charcount']), color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 슬롯 부족]')
                return
            cmgr.add_character_with_raw(ctx.author.id, charname, chartype, self.templates['baseitem'], self.templates['basestat'], {})
            if charcount == 0:
                cmgr.change_character(ctx.author.id, charname)
                desc = '첫 캐릭터 생성이네요, 이제 게임을 시작해보세요!'
            else:
                desc = '`{}캐릭터 변경` 명령으로 이 캐릭터를 선텍해 게임을 시작할 수 있습니다!'.format(self.prefix)
            await ctx.send(embed=discord.Embed(title='{} 캐릭터를 생성했습니다! - `{}`'.format(self.emj.get(ctx, 'check'), charname), description=desc, color=self.color['success']))
            self.msglog.log(ctx, '[캐릭터 생성: 완료]')

    @_char.command(name='변경', aliases=['선택', '변', '선'])
    async def _char_change(self, ctx: commands.Context, *, name):
        cmgr = CharMgr(self.cur)
        char = list(filter(lambda x: x.name.lower() == name.lower(), cmgr.get_chars(ctx.author.id)))
        if char:
            cname = char[0].name
            if not char[0].online:
                if not cmgr.is_being_forgotten(cname):
                    cmgr.change_character(ctx.author.id, cname)
                    await ctx.send(embed=discord.Embed(title='{} 현재 캐릭터를 `{}` 으로 변경했습니다!'.format(self.emj.get(ctx, 'check'), cname), color=self.color['success']))
                else:
                    await ctx.send(embed=discord.Embed(title=f'❓ 삭제 중인 캐릭터입니다: `{cname}`', description='이 캐릭터는 삭제 중이여서 로그인할 수 없습니다. `{}캐릭터 삭제취소` 명령으로 취소할 수 있습니다.'.format(self.prefix), color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 변경: 삭제 중인 캐릭터]')
            else:
                await ctx.send(embed=discord.Embed(title=f'❓ 이미 현재 캐릭터입니다: `{cname}`', description='이 캐릭터는 현재 플레이 중인 캐릭터입니다.', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 변경: 이미 현재 캐릭터]')
        else:
            await ctx.send(embed=errembeds.CharNotFound.getembed(ctx, cname))
            self.msglog.log(ctx, '[캐릭터 변경: 존재하지 않는 캐릭터]')

    @_char.command(name='삭제', aliases=['삭'])
    async def _char_delete(self, ctx: commands.Context, *, name):
        cmgr = CharMgr(self.cur)
        char = list(filter(lambda x: x.name.lower() == name.lower(), cmgr.get_chars(ctx.author.id)))
        if not char:
            embed = errembeds.CharNotFound.getembed(ctx, name)
            embed.description = '캐릭터 이름이 정확한지 확인해주세요!\n또는 캐릭터가 이미 삭제되었을 수도 있습니다.'
            await ctx.send(embed=embed)
            self.msglog.log(ctx, '[캐릭터 삭제: 존재하지 않는 캐릭터]')
            return
        cname = char[0].name
        if cmgr.is_being_forgotten(name):
            await ctx.send(embed=discord.Embed(title=f'❓ 이미 삭제가 요청된 캐릭터입니다: `{cname}`', description=f'삭제를 취소하려면 `{self.prefix}캐릭터 삭제취소` 명령을 입력하세요.', color=self.color['error']))
            self.msglog.log(ctx, '[캐릭터 삭제: 이미 삭제 요청됨]')
            return
        msg = await ctx.send(embed=discord.Embed(
            title=f'⚠ `{cname}` 캐릭터를 정말로 삭제할까요?',
            description=f'캐릭터는 삭제 버튼을 누른 후 24시간 후에 완전히 지워지며, 이 기간 동안에 `{self.prefix}캐릭터 삭제취소` 명령으로 취소가 가능합니다.',
            color=self.color['warn']
        ))
        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        self.msglog.log(ctx, '[캐릭터 삭제: 캐릭터 삭제 경고]')
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info'])
            embed.set_footer(text='이 메시지는 7초 후에 삭제됩니다.')
            await ctx.send(embed=embed, delete_after=7)
            self.msglog.log(ctx, '[캐릭터 삭제: 시간 초과]')
        else:
            remj = str(reaction.emoji)
            if remj == '⭕':
                cmgr.schedule_delete(ctx.author.id, cname)
                await ctx.send(embed=discord.Embed(
                    title='{} `{}` 캐릭터가 24시간 후에 완전히 지워집니다.'.format(self.emj.get(ctx, 'check'), cname),
                    description=f'24시간 후에 완전히 지워지며, 이 기간 동안에 `{self.prefix}캐릭터 삭제취소` 명령으로 취소가 가능합니다.',
                    color=self.color['success']
                ))
                self.msglog.log(ctx, '[캐릭터 삭제: 삭제 작업 예약됨]')
            elif remj == '❌':
                await ctx.send(embed=discord.Embed(title=f'❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 삭제: 취소됨]')

    @_char.command(name='삭제취소')
    async def _char_cancel_delete(self, ctx: commands.Context, *, name):
        cmgr = CharMgr(self.cur)
        char = list(filter(lambda x: x.name.lower() == name.lower(), cmgr.get_chars(ctx.author.id)))
        if not char:
            embed = errembeds.CharNotFound.getembed(ctx, name)
            embed.description = '캐릭터 이름이 정확한지 확인해주세요!\n또는 캐릭터가 이미 삭제되었을 수도 있습니다.'
            await ctx.send(embed=embed)
            self.msglog.log(ctx, '[캐릭터 삭제취소: 존재하지 않는 캐릭터]')
            return
        cname = char[0].name
        if not cmgr.is_being_forgotten(cname):
            await ctx.send(embed=discord.Embed(title=f'❓ 삭제중이 아닌 캐릭터입니다: `{cname}`', description='이 캐릭터는 삭제 중인 캐릭터가 아닙니다.', color=self.color['error']))
            self.msglog.log(ctx, '[캐릭터 삭제취소: 삭제중이 아닌 캐릭터]')
            return
        cmgr.cancel_delete(cname)
        await ctx.send(embed=discord.Embed(title='{} 캐릭터 삭제를 취소했습니다!: `{}`'.format(self.emj.get(ctx, 'check'), cname), color=self.color['success']))
        self.msglog.log(ctx, '[캐릭터 삭제취소: 삭제 취소 완료]')
        return

    @commands.command(name='캐생', aliases=['새캐'])
    async def _w_char_create(self, ctx: commands.Context):
        await self._char_create(ctx)

    @commands.command(name='캐삭')
    async def _w_char_delete(self, ctx: commands.Context, *, name):
        await self._char_delete(ctx, name=name)

    @_char_change.error
    @_char_delete.error
    @_w_char_delete.error
    @_char_cancel_delete.error
    async def _e_char(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'name':
                missing = '캐릭터의 이름'
            await ctx.send(embed=errembeds.MissingArgs.getembed(self.prefix, self.color['error'], missing))

    @commands.command(name='이름변경', aliases=['닉변'])
    async def _char_changename(self, ctx: commands.Context, *, charname: typing.Optional[str]):
        cmgr = CharMgr(self.cur)
        if charname:
            char = cmgr.get_character(charname, ctx.author.id)
            if not char:
                await ctx.send(embed=errembeds.CharNotFound.getembed(ctx, charname))
                self.msglog.log(ctx, '[이름변경: 존재하지 않는 캐릭터]')
                return
        else:
            char = cmgr.get_current_char(ctx.author.id)
        td = datetime.datetime.now() - char.last_nick_change
        if td <= datetime.timedelta(days=1):
            cldstr = ' '.join(timedelta.format_timedelta(datetime.timedelta(days=1) - td).values())
            await ctx.send(embed=discord.Embed(title='⏱ 쿨타임 중입니다!', description=f'**`{cldstr}` 남았습니다!**\n닉네임은 24시간에 한 번 변경할 수 있습니다.', color=self.color['info']))
            self.msglog.log(ctx, '[이름변경: 쿨다운 중]')
            return
        await ctx.send(embed=discord.Embed(title='🏷 캐릭터 이름 변경', description=f'`{char.name}` 캐릭터의 이름을 변경합니다. 새 이름을 입력해주세요!\n취소하려면 `취소`를 입력하세요.', color=self.color['ask']))
        self.msglog.log(ctx, '[이름변경]')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content
        try:
            m = await self.client.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            embed = discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info'])
            embed.set_footer(text='이 메시지는 7초 후에 삭제됩니다.')
            await ctx.send(embed=embed, delete_after=7)
            self.msglog.log(ctx, '[이름변경: 시간 초과]')
        else:
            if m.content == '취소':
                await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[이름변경: 취소됨]')
                return
            elif not (2 <= len(m.content) <= 10):
                await ctx.send(embed=discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='캐릭터 이름은 2글자 이상이여야 합니다.\n다시 시도해 주세요!', color=self.color['error']))
                self.msglog.log(ctx, '[이름변경: 너무 짧은 이름]')
                return
            elif not re.match('^[ |가-힣|a-z|A-Z|0-9]+$', m.content):
                await ctx.send(embed=discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='캐릭터 이름은 반드시 한글, 영어, 숫자만을 사용해야 합니다.\n다시 시도해 주세요!', color=self.color['error']))
                self.msglog.log(ctx, '[이름변경: 올바르지 않은 이름]')
                return
            elif self.cur.execute('select * from chardata where name=%s', m.content) != 0:
                await ctx.send(embed=discord.Embed(title='❌ 이미 사용중인 이름입니다!', description='다시 시도해 주세요!', color=self.color['error']))
                self.msglog.log(ctx, '[이름변경: 이미 사용중인 이름]')
                return
            else:
                for pfx in self.client.command_prefix:
                    if pfx.rstrip().lower() in m.content.lower():
                        await ctx.send(embed=discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='아젤리아 봇 접두사는 이름에 포함할 수 없습니다.\n다시 시도해 주세요!', color=self.color['error']))
                        self.msglog.log(ctx, '[이름변경: 접두사 포함 금지]')
                        return
                newname = m.content
            msg = await ctx.send(embed=discord.Embed(title=f'🏷 `{newname}` 으로 변경할까요?', description='변경하면 24시간 후에 다시 변경할 수 있습니다!', color=self.color['ask']))
            emjs = ['⭕', '❌']
            for em in emjs:
                await msg.add_reaction(em)
            def oxcheck(reaction, user):
                return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=oxcheck, timeout=20)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except:
                    pass
            else:
                if reaction.emoji == '⭕':
                    self.cur.execute('update chardata set name=%s, last_nick_change=%s where name=%s', (newname, datetime.datetime.now(), char.name))
                    await ctx.send(embed=discord.Embed(title='{} `{}` 으로 변경했습니다!'.format(self.emj.get(ctx, 'check'), newname), color=self.color['success']))
                    self.msglog.log(ctx, '[이름변경: 완료]')
                elif reaction.emoji == '❌':
                    await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))
                    self.msglog.log(ctx, '[이름변경: 취소됨]')

    @commands.command(name='로그아웃')
    async def _logout(self, ctx: commands.Context):
        cmgr = CharMgr(self.cur)
        char = cmgr.get_current_char(ctx.author.id)
        msg = await ctx.send(embed=discord.Embed(
            title='📤 로그아웃',
            description=f'`{char.name}` 캐릭터에서 로그아웃할까요?\n`{self.prefix}캐릭터 변경` 명령으로 다시 캐릭터에 접속할 수 있습니다.',
            color=self.color['ask']
        ))
        self.msglog.log(ctx, '[로그아웃]')
        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        def oxcheck(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', check=oxcheck, timeout=20)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
        else:
            if reaction.emoji == '⭕':
                cmgr.logout_all(ctx.author.id)
                await ctx.send(embed=discord.Embed(title='{} 로그아웃했습니다!'.format(self.emj.get(ctx, 'check')), description=f'`{self.prefix}캐릭터 변경` 명령으로 다시 캐릭터에 접속할 수 있습니다.', color=self.color['success']))
                self.msglog.log(ctx, '[로그아웃: 완료]')
            elif reaction.emoji == '❌':
                await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[로그아웃: 취소됨]')

def setup(client):
    cog = Charcmds(client)
    client.add_cog(cog)