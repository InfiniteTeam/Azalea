import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import re
import json
from exts.utils import pager, itemmgr, emojibuttons, errors, charmgr
from exts.utils.basecog import BaseCog
from templates import errembeds

class InGamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            if cmd.name not in ['캐릭터', '로그아웃']:
                cmd.add_check(self.check.char_online)

    async def backpack_embed(self, ctx, pgr: pager.Pager):
        items = pgr.get_thispage()
        itemstr = ''
        for one in items:
            founditem = self.imgr.fetch_itemdb_by_id(one['id'])
            icon = founditem['icon']['default']
            name = founditem['name']
            count = one['count']
            itemstr += '{} **{}** ({}개)\n'.format(icon, name, count)
        embed = discord.Embed(
            title=f'💼 `{ctx.author.name}`님의 가방',
            color=self.color['info'],
            timestamp=datetime.datetime.utcnow()
        )
        if items:
            embed.description = itemstr + '```{}/{} 페이지, 전체 {}개```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
        else:
            embed.description = '\n가방에 아무것도 없네요! ~~아, 공기는 있어요!~~'
        return embed

    @commands.command(name='가방', aliases=['템'])
    async def _backpack(self, ctx: commands.Context):
        perpage = 4
        items = self.imgr.get_useritems(ctx.author.id)
        
        print(items)
        pgr = pager.Pager(items, perpage=perpage)
        msg = await ctx.send(embed=await self.backpack_embed(ctx, pgr))
        self.msglog.log(ctx, '[가방]')
        for emj in emojibuttons.PageButton.emojis:
            await msg.add_reaction(emj)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emojibuttons.PageButton.emojis
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
            except asyncio.TimeoutError:
                pass
            else:
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                if asyncio.iscoroutine(do):
                    await asyncio.gather(do,
                        msg.edit(embed=await self.backpack_embed(ctx, pgr)),
                    )

    async def char_embed(self, ctx: commands.Context, pgr: pager.Pager):
        chars = pgr.get_thispage()
        charstr = ''
        for one in chars:
            name = one['name']
            level = one['level']
            chartype = charmgr.CharType.format_chartype(one['type'])
            online = one['online']
            onlinestr = ''
            if online:
                onlinestr = '(**현재 플레이중**)'
            charstr += '**{}** {}\n레벨: `{}` \\| 직업: `{}`\n\n'.format(name, onlinestr, level, chartype)
        embed = discord.Embed(
            title=f'🎲 `{ctx.author.name}`님의 캐릭터 목록',
            description=charstr,
            color=self.color['info'],
            timestamp=datetime.datetime.utcnow()
        )
        embed.description = charstr + '```{}/{} 페이지, 전체 {}캐릭터```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
        return embed

    @commands.group(name='캐릭터', aliases=['캐'], invoke_without_command=True)
    async def _char(self, ctx: commands.Context):
        perpage = 5
        cmgr = charmgr.CharMgr(self.cur, ctx.author.id)
        chars = cmgr.get_characters()
        if not chars:
            await ctx.send(embed=discord.Embed(
                title='🎲 캐릭터가 하나도 없네요!',
                description='`{}생성` 명령으로 캐릭터를 생성해서 게임을 시작하세요!'.format(self.prefix),
                color=self.color['warn'],
                timestamp=datetime.datetime.utcnow()
            ))
            return
        pgr = pager.Pager(chars, perpage)
        msg = await ctx.send(embed=await self.char_embed(ctx, pgr))
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
                pass
            else:
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                if asyncio.iscoroutine(do):
                    await asyncio.gather(do,
                        msg.edit(embed=await self.char_embed(ctx, pgr)),
                    )

    @_char.command(name='생성', aliases=['생'])
    async def _char_creacte(self, ctx:commands.Context):
        self._char_creacte.name = '생성'
        cmgr = charmgr.CharMgr(self.cur, ctx.author.id)
        charcount = len(cmgr.get_characters())
        if charcount >= self.config['max_charcount']:
            await ctx.send(embed=discord.Embed(title='❌ 캐릭터 슬롯이 모두 찼습니다.', description='유저당 최대 캐릭터 수는 {}개 입니다.'.format(self.config['max_charcount']), color=self.color['error']))
            self.msglog.log(ctx, '[캐릭터 슬롯 부족]')
            return
        namemsg = await ctx.send(embed=discord.Embed(title='🏷 캐릭터 생성 - 이름', description='새 캐릭터를 생성합니다. 캐릭터의 이름을 입력하세요.\n취소하려면 `취소` 를 입력하세요!', color=self.color['ask']))
        self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기]')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content
        try:
            m = await self.client.wait_for('message', check=check, timeout=60*5)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
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
            elif not re.match('^[ |가-힣|a-z|A-Z|0-9|\*]+$', m.content):
                await ctx.send(embed=discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='캐릭터 이름은 반드시 한글, 영어, 숫자만을 사용해야 합니다.\n다시 시도해 주세요!', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 올바르지 않은 이름]')
                return
            elif self.cur.execute('select * from chardata where name=%s', m.content) != 0:
                await ctx.send(embed=discord.Embed(title='❌ 이미 사용중인 이름입니다!', description='다시 시도해 주세요!', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 이미 사용중인 이름]')
                return
            else:
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
            reaction, user = await self.client.wait_for('reaction_add', check=rcheck, timeout=60*5)
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info']))
            self.msglog.log(ctx, '[캐릭터 생성: 직업 선택: 시간 초과]')
        else:
            e = str(reaction.emoji)
            if e == '❌':
                await ctx.send(embed=discord.Embed(title='❌ 취소되었습니다.', color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 직업 선택: 취소됨]')
                return
            elif e == '⚔':
                chartype = charmgr.CharType.Knight()
            elif e == '🏹':
                chartype = charmgr.CharType.Archer()
            elif e == '🔯':
                chartype = charmgr.CharType.Wizard()
            
            charcount = len(cmgr.get_characters())
            if charcount >= self.config['max_charcount']:
                await ctx.send(embed=discord.Embed(title='❌ 캐릭터 슬롯이 모두 찼습니다.', description='유저당 최대 캐릭터 수는 {}개 입니다.'.format(self.config['max_charcount']), color=self.color['error']))
                self.msglog.log(ctx, '[캐릭터 생성: 슬롯 부족]')
                return
            cmgr.add_character(charname, chartype, self.templates['baseitem'])
            if charcount == 0:
                cmgr.change_character(charname)
                desc = '첫 캐릭터 생성이네요, 이제 게임을 시작해보세요!'
            else:
                desc = '`{}캐릭터 변경` 명령으로 이 캐릭터를 선텍해 게임을 시작할 수 있습니다!'.format(self.prefix)
            await ctx.send(embed=discord.Embed(title='{} 캐릭터를 생성했습니다! - `{}`'.format(self.emj.get(ctx, 'check'), charname), description=desc, color=self.color['success']))
            self.msglog.log(ctx, '[캐릭터 생성: 완료]')

    @_char.command(name='변경')
    async def _char_change(self, ctx: commands.Context, *, name):
        cmgr = charmgr.CharMgr(self.cur, ctx.author.id)
        char = list(filter(lambda x: x['name'] == name, cmgr.get_characters()))
        if char:
            if not char[0]['online']:
                cmgr.change_character(name)
                await ctx.send(embed=discord.Embed(title='{} 현재 캐릭터를 `{}` 으로 변경했습니다!'.format(self.emj.get(ctx, 'check'), name), color=self.color['success']))
            else:
                await ctx.send(embed=discord.Embed(title=f'❓ 이미 현재 캐릭터입니다: `{name}`', description='이 캐릭터는 현재 플레이 중인 캐릭터입니다.', color=self.color['warn']))
                self.msglog.log(ctx, '[캐릭터 변경: 이미 현재 캐릭터]')
        else:
            await ctx.send(embed=discord.Embed(title=f'❓ 존재하지 않는 캐릭터입니다: `{name}`', description='캐릭터 이름이 정확한지 확인해주세요!', color=self.color['error']))
            self.msglog.log(ctx, '[캐릭터 변경: 존재하지 않는 캐릭터]')

    @_char_change.error
    async def _e_char_change(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'name':
                missing = '캐릭터의 이름'
            await ctx.send(embed=errembeds.MissingArgs.getembed(self.prefix, self.color['error'], missing))

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)