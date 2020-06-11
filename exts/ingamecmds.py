import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import typing
import re
import random
import json
from exts.utils import pager, emojibuttons, errors, timedelta
from exts.utils.basecog import BaseCog
from templates import errembeds
from dateutil.relativedelta import relativedelta
from exts.utils.datamgr import CharMgr, ItemMgr, ItemDBMgr, CharacterType, CharacterData, ItemData, SettingData, Setting, SettingDBMgr, SettingMgr

class InGamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            if cmd.name not in ['캐릭터', '로그아웃', '캐생', '캐삭']:
                cmd.add_check(self.check.char_online)

    async def backpack_embed(self, ctx, pgr: pager.Pager, charname, mode='default'):
        items = pgr.get_thispage()
        itemstr = ''
        moneystr = ''
        cmgr = CharMgr(self.cur)
        char = cmgr.get_character(charname)
        idb = ItemDBMgr(self.datadb)
        for idx in range(len(items)):
            one = items[idx]
            founditem = idb.fetch_item(one.id)
            icon = founditem.icon
            name = founditem.name
            count = one.count
            if mode == 'select':
                itemstr += '{}. {} **{}** ({}개)\n'.format(idx+1, icon, name, count)
            else:
                itemstr += '{} **{}** ({}개)\n'.format(icon, name, count)
        embed = discord.Embed(
            title=f'💼 `{charname}`의 가방',
            color=self.color['info']
        )
        moneystr = f'\n**💵 {char.money} 골드**'
        if mode == 'select':
            moneystr = ''
            embed.title += ' - 선택 모드'
        if items:
            embed.description = itemstr + moneystr + '```{}/{} 페이지, 전체 {}개```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
        else:
            embed.description = '\n가방에는 공기 말고는 아무것도 없네요!'
        return embed

    @commands.command(name='가방', aliases=['템', '아이템'])
    @commands.guild_only()
    async def _backpack(self, ctx: commands.Context, *, charname: typing.Optional[str]=None):
        perpage = 8
        cmgr = CharMgr(self.cur)
        if charname:
            char = cmgr.get_character(charname)
            if char:
                imgr = ItemMgr(self.cur, char.name)
            else:
                await ctx.send(embed=errembeds.CharNotFound.getembed(ctx, charname))
                self.msglog.log(ctx, '[가방: 존재하지 않는 캐릭터]')
                return
        else:
            char = cmgr.get_current_char(ctx.author.id)
            charname = char.name
            imgr = ItemMgr(self.cur, charname)
        items = imgr.get_items()
        
        pgr = pager.Pager(items, perpage=perpage)
        msg = await ctx.send(embed=await self.backpack_embed(ctx, pgr, charname, 'default'))
        self.msglog.log(ctx, '[가방]')
        extemjs = ['❔']
        owner = False
        if char.id == ctx.author.id:
            owner = True
            extemjs.append('🗑')
        emjs = emojibuttons.PageButton.emojis + extemjs
        async def addreaction(m):
            if len(pgr.pages()) <= 1:
                for emj in extemjs:
                    await m.add_reaction(emj)
            else:
                for emj in emjs:
                    await m.add_reaction(emj)
        await addreaction(msg)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emjs
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except discord.Forbidden:
                    pass
                finally:
                    break
            else:
                if reaction.emoji in extemjs:
                    async def wait_for_cancel(msg):
                        def cancelcheck(reaction, user):
                            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in ['❌']
                        try:
                            reaction, user = await self.client.wait_for('reaction_add', check=cancelcheck, timeout=20)
                        except asyncio.TimeoutError:
                            pass
                        else:
                            embed = discord.Embed(title='❗ 취소되었습니다.', color=self.color['error'])
                            embed.set_footer(text='이 메시지는 7초후 삭제됩니다')
                            await ctx.send(embed=embed, delete_after=7)
                            self.msglog.log(ctx, '[가방/아이템정보: 아이템 번쨰 입력: 취소됨]')
                            return True
                        finally:
                            try:
                                await msg.delete()
                            except:
                                pass

                    def msgcheck(m):
                        return m.author == ctx.author and m.channel == ctx.channel and m.content
                    
                    async def wait_for_itemindex(askmsg):
                        try:
                            m = await self.client.wait_for('message', check=msgcheck, timeout=20)
                        except asyncio.TimeoutError:
                            return asyncio.TimeoutError
                        else:
                            nowpage = pgr.get_thispage()
                            if not m.content.isdecimal():
                                embed = discord.Embed(title='❌ 숫자만을 입력해주세요!', color=self.color['error'])
                                embed.set_footer(text='이 메시지는 7초후 삭제됩니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[가방: 아이템 번쨰 입력: 숫자만 입력]')
                            else:
                                idx = int(m.content)
                                if 1 <= idx <= len(nowpage):
                                    return int(m.content)
                                else:
                                    embed = discord.Embed(
                                        title='❓ 아이템 번째수가 올바르지 않습니다!',
                                        description='위의 가방 메시지에 아이템 앞마다 번호가 있습니다.',
                                        color=self.color['error']
                                    )
                                    embed.set_footer(text='이 메시지는 7초후 삭제됩니다')
                                    await ctx.send(embed=embed, delete_after=7)
                                    self.msglog.log(ctx, '[가방: 아이템 번쨰 입력: 올바르지 않은 번째수]')
                        finally:
                            try:
                                await askmsg.delete()
                            except:
                                pass

                    async def wait_for_itemcount(askmsg, idx):
                        try:
                            m = await self.client.wait_for('message', check=msgcheck, timeout=20)
                        except asyncio.TimeoutError:
                            return asyncio.TimeoutError
                        else:
                            nowpage = pgr.get_thispage()
                            
                            if m.content in ['모두', '전부']:
                                return nowpage[idx].count
                            elif m.content.isdecimal() and 1 <= int(m.content) <= nowpage[idx].count:
                                return int(m.content)
                            elif not m.content.isdecimal():
                                embed = discord.Embed(title='❌ 숫자만을 입력해주세요!', color=self.color['error'])
                                embed.set_footer(text='이 메시지는 7초후 삭제됩니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[가방: 아이템 번쨰 입력: 숫자만 입력]')
                            else:
                                embed = discord.Embed(
                                    title='❓ 입력한 개수가 올바르지 않거나 총 개수보다 많습니다!',
                                    description='아이템 개수는 최소 1개, 아이템의 총 개수 이하여야 합니다.\n`모두` 를 입력해 전부 버릴 수 있습니다.',
                                    color=self.color['error']
                                )
                                embed.set_footer(text='이 메시지는 7초후 삭제됩니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[가방: 아이템 번쨰 입력: 올바르지 않은 개수]')
                        finally:
                            try:
                                await askmsg.delete()
                            except:
                                pass

                    async def looper(canceltask, msgtask):
                        while True:
                            if canceltask.done():
                                msgtask.cancel()
                                return canceltask
                            elif msgtask.done():
                                canceltask.cancel()
                                return msgtask
                            await asyncio.sleep(0.1)

                    oxemjs = [self.emj.get(ctx, 'check'), self.emj.get(ctx, 'cross')]

                    if ctx.channel.last_message_id == msg.id:
                        await msg.edit(embed=await self.backpack_embed(ctx, pgr, charname, 'select'))
                    else:
                        results = await asyncio.gather(
                            msg.delete(),
                            ctx.send(embed=await self.backpack_embed(ctx, pgr, charname, 'select'))
                        )
                        msg = results[1]
                        await addreaction(msg)
                        reaction.message = msg

                if reaction.emoji == '🗑' and owner:
                    delmsg = await ctx.send(embed=discord.Embed(
                        title='📮 아이템 버리기 - 버릴 아이템의 번호를 선택하세요!',
                        description='위의 가방 메시지에 아이템 앞마다 번호가 있습니다.\n또는 ❌ 버튼을 클릭해 취소할 수 있습니다.',
                        color=self.color['ask']
                    ))
                    await delmsg.add_reaction('❌')
                    self.msglog.log(ctx, '[가방/아이템버리기: 버릴 아이템 번호 선택]')
                    canceltask = asyncio.create_task(wait_for_cancel(delmsg))
                    msgtask = asyncio.create_task(wait_for_itemindex(delmsg))
                    rst = await looper(canceltask, msgtask)

                    count = 1

                    if rst == msgtask and type(msgtask.result()) == int:
                        idx = msgtask.result()
                        nowpage = pgr.get_thispage()
                        selected_item = nowpage[idx-1]

                        delcountmsg = await ctx.send(embed=discord.Embed(
                            title='📮 아이템 버리기 - 몇 개를 버릴까요? (최대 {}개)'.format(selected_item.count),
                            description='아이템 개수는 최소 1개, 아이템의 총 개수 이하여야 합니다.\n`모두` 를 입력해 전부 버릴 수 있습니다.\n또는 ❌ 버튼을 클릭해 취소할 수 있습니다.',
                            color=self.color['ask']
                        ))
                        await delcountmsg.add_reaction('❌')
                        self.msglog.log(ctx, '[가방/아이템버리기: 버릴 아이템 개수 선택]')
                        canceltask = asyncio.create_task(wait_for_cancel(delcountmsg))
                        counttask = asyncio.create_task(wait_for_itemcount(delcountmsg, idx-1))
                        rst = await looper(canceltask, counttask)
                        if rst == counttask and type(msgtask.result()) == int:
                            count = counttask.result()

                        if rst == counttask and type(counttask.result()) == int:

                            idx = msgtask.result()
                            nowpage = pgr.get_thispage()
                            selected_item = nowpage[idx-1]
                            idgr = ItemDBMgr(self.datadb)
                            item = idgr.fetch_item(selected_item.id)
                            embed = discord.Embed(title=item.icon + ' ' + item.name, description='**아이템을 버리면 다시 회수할 수 없습니다.** 계속할까요?', color=self.color['info'])
                            embed.set_author(name='⚠ 이 아이템을 버립니다.')
                            enchantstr = ''
                            for enchant in selected_item.enchantments:
                                enchantstr += '{}: {}\n'.format(enchant.name, enchant.level)
                            if not enchantstr:
                                enchantstr = '없음'
                            embed.add_field(name='아이템 설명', value=item.description)
                            embed.add_field(name='마법부여', value=enchantstr)
                            embed.add_field(name='버릴 개수', value='{}개'.format(count))
                            itemdelmsg = await ctx.send(embed=embed)
                            for em in oxemjs:
                                await itemdelmsg.add_reaction(em)

                            def oxcheck(reaction, user):
                                return user == ctx.author and itemdelmsg.id == reaction.message.id and reaction.emoji in oxemjs

                            async def wait_for_delete_ox():
                                try:
                                    reaction, user = await self.client.wait_for('reaction_add', check=oxcheck, timeout=20)
                                except asyncio.TimeoutError:
                                    return asyncio.TimeoutError
                                else:
                                    if reaction.emoji == oxemjs[0]:
                                        imgr.delete_item(selected_item, count=count)
                                        embed = discord.Embed(title='{} 아이템을 버렸습니다!'.format(self.emj.get(ctx, 'check')), color=self.color['success'])
                                        embed.set_footer(text='이 메시지는 7초 후에 삭제됩니다')
                                        await ctx.send(embed=embed, delete_after=7)
                                    elif reaction.emoji == oxemjs[1]:
                                        embed = discord.Embed(title='❌ 취소되었습니다.', color=self.color['error'])
                                        embed.set_footer(text='이 메시지는 7초 후에 삭제됩니다')
                                        await ctx.send(embed=embed, delete_after=7)
                                finally:
                                    try:
                                        await itemdelmsg.delete()
                                    except:
                                        pass

                            await wait_for_delete_ox()
                            
                    elif rst == msgtask and msgtask.result() == asyncio.TimeoutError:
                        embed = discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info'])
                        embed.set_footer(text='이 메시지는 7초 후에 삭제됩니다.')
                        await ctx.send(embed=embed, delete_after=7)
                        self.msglog.log(ctx, '[가방: 시간 초과]')

                elif reaction.emoji == '❔':
                    infomsg = await ctx.send(embed=discord.Embed(
                        title='🔍 아이템 정보 - 자세한 정보를 볼 아이템의 번호를 선택하세요!',
                        description='위의 가방 메시지에 아이템 앞마다 번호가 있습니다.\n또는 ❌ 버튼을 클릭해 취소할 수 있습니다.',
                        color=self.color['ask']
                    ))
                    await infomsg.add_reaction('❌')
                    self.msglog.log(ctx, '[가방/아이템정보: 아이템 번쨰 입력]')
                    canceltask = asyncio.create_task(wait_for_cancel(infomsg))
                    msgtask = asyncio.create_task(wait_for_itemindex(infomsg))
                    rst = await looper(canceltask, msgtask)
                    
                    if rst == msgtask and type(msgtask.result()) == int:
                        idx = msgtask.result()
                        nowpage = pgr.get_thispage()
                        selected_item = nowpage[idx-1]
                        idgr = ItemDBMgr(self.datadb)
                        item = idgr.fetch_item(selected_item.id)
                        embed = discord.Embed(title=item.icon + ' ' + item.name, description=item.description, color=self.color['info'])
                        embed.set_author(name='📔 아이템 상세 정보')
                        enchantstr = ''
                        for enchant in selected_item.enchantments:
                            enchantstr += '{}: {}\n'.format(enchant.name, enchant.level)
                        if not enchantstr:
                            enchantstr = '없음'
                        embed.add_field(name='마법부여', value=enchantstr)
                        embed.add_field(name='개수', value='{}개'.format(selected_item.count))
                        embed.set_footer(text='❌ 버튼을 클릭해 이 메시지를 닫습니다. 5분 후에 버튼이 사라집니다.')
                        iteminfomsg = await ctx.send(embed=embed)
                        await iteminfomsg.add_reaction('❌')
                        self.msglog.log(ctx, '[가방/아이템정보]')
                        async def wait_for_close_iteminfo():
                            def cancelcheck(reaction, user):
                                return user == ctx.author and iteminfomsg.id == reaction.message.id and reaction.emoji in ['❌']
                            try:
                                reaction, user = await self.client.wait_for('reaction_add', check=cancelcheck, timeout=60*5)
                            except asyncio.TimeoutError:
                                try:
                                    await iteminfomsg.clear_reactions()
                                except:
                                    pass
                            else:
                                await iteminfomsg.delete()
                        await wait_for_close_iteminfo()
                    elif rst == msgtask and msgtask.result() == asyncio.TimeoutError:
                        embed = discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info'])
                        embed.set_footer(text='이 메시지는 7초 후에 삭제됩니다.')
                        await ctx.send(embed=embed, delete_after=7)
                        self.msglog.log(ctx, '[가방: 시간 초과]')
                
                pgr.set_obj(imgr.get_items())
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                await asyncio.gather(do,
                    msg.edit(embed=await self.backpack_embed(ctx, pgr, charname, 'default')),
                )

    async def char_embed(self, username, pgr: pager.Pager, mode='default'):
        chars = pgr.get_thispage()
        charstr = ''
        for idx in range(len(chars)):
            one = chars[idx]
            name = one.name
            if mode == 'select':
                name = f'{idx+1}. {name}'
            level = one.level
            chartype = one.type.value
            online = one.online
            onlinestr = ''
            if online:
                onlinestr = '(**현재 플레이중**)'
            deleteleftstr = ''
            if one.delete_request:
                tdleft = timedelta.format_timedelta((one.delete_request + relativedelta(hours=24)) - datetime.datetime.now())
                deleteleft = ' '.join(tdleft.values())
                deleteleftstr = '\n**`{}` 후에 삭제됨**'.format(deleteleft)
            charstr += '**{}** {}\n레벨: `{}` \\| 직업: `{}` {}\n\n'.format(name, onlinestr, level, chartype, deleteleftstr)
        embed = discord.Embed(
            title=f'🎲 `{username}`님의 캐릭터 목록',
            description=charstr,
            color=self.color['info']
        )
        embed.description = charstr + '```{}/{} 페이지, 전체 {}캐릭터```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
        return embed

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
        msg = await ctx.send(embed=await self.char_embed(user.name, pgr))
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
                        msg.edit(embed=await self.char_embed(user.name, pgr)),
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
            cmgr.add_character_with_raw(ctx.author.id, charname, chartype, self.templates['baseitem'], self.templates['basestat'], self.datadb.get_base_settings())
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

    async def char_settings_embed(self, char: CharacterData, mode='default'):
        sdgr = SettingDBMgr(self.datadb)
        smgr = SettingMgr(self.cur, sdgr, char)
        settitles = []
        setvalue = []
        for idx in range(len(self.datadb.settings)):
            st = self.datadb.settings[idx]
            settitles.append(st.title)
            valuestr = str(smgr.get_setting(st.name))
            for x in [('True', '켜짐'), ('False', '꺼짐')]:
                valuestr = valuestr.replace(x[0], x[1])
            setvalue.append(valuestr)
        embed = discord.Embed(title='⚙ `{}` 캐릭터 설정'.format(char.name), color=self.color['info'])
        if mode == 'select':
            embed.title += ' - 선택 모드'
            embed.add_field(name='번호', value='\n'.join(map(str, range(1, len(self.datadb.settings)+1))))
        embed.add_field(name='설정 이름', value='\n'.join(settitles))
        embed.add_field(name='설정값', value='\n'.join(setvalue))
        return embed

    @commands.group(name='설정', aliases=['셋', '설'], invoke_without_command=True)
    async def _char_settings(self, ctx: commands.Context, *, charname: typing.Optional[str]=None):
        cmgr = CharMgr(self.cur)
        if charname:
            char = cmgr.get_character(charname, ctx.author.id)
            if not char:
                await ctx.send(embed=errembeds.CharNotFound.getembed(ctx, charname))
                return
        else:
            char = cmgr.get_current_char(ctx.author.id)
        
        msg = await ctx.send(embed=await self.char_settings_embed(char))
        emjs = ['✏']
        async def addreaction(msg):
            for em in emjs:
                await msg.add_reaction(em)
        await addreaction(msg)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emjs
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except:
                    pass
            else:
                async def wait_for_cancel(msg):
                    def cancelcheck(reaction, user):
                        return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in ['❌']
                    try:
                        reaction, user = await self.client.wait_for('reaction_add', check=cancelcheck, timeout=20)
                    except asyncio.TimeoutError:
                        pass
                    else:
                        embed = discord.Embed(title='❗ 취소되었습니다.', color=self.color['error'])
                        embed.set_footer(text='이 메시지는 7초후 삭제됩니다')
                        await ctx.send(embed=embed, delete_after=7)
                        self.msglog.log(ctx, '[설정: 번쨰 입력: 취소됨]')
                        return True
                    finally:
                        try:
                            await msg.delete()
                        except:
                            pass

                def msgcheck(m):
                    return m.author == ctx.author and m.channel == ctx.channel and m.content
                
                async def wait_for_setindex(askmsg):
                    try:
                        m = await self.client.wait_for('message', check=msgcheck, timeout=20)
                    except asyncio.TimeoutError:
                        return asyncio.TimeoutError
                    else:
                        if not m.content.isdecimal():
                            embed = discord.Embed(title='❌ 숫자만을 입력해주세요!', color=self.color['error'])
                            embed.set_footer(text='이 메시지는 7초후 삭제됩니다')
                            await ctx.send(embed=embed, delete_after=7)
                            self.msglog.log(ctx, '[설정: 번쨰 입력: 숫자만 입력]')
                        else:
                            idx = int(m.content)
                            if 1 <= idx <= len(self.datadb.settings):
                                return int(m.content)
                            else:
                                embed = discord.Embed(
                                    title='❓ 설정항목 번째수가 올바르지 않습니다!',
                                    description='위의 메시지에 항목 앞마다 번호가 있습니다.',
                                    color=self.color['error']
                                )
                                embed.set_footer(text='이 메시지는 7초후 삭제됩니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[설정: 번쨰 입력: 올바르지 않은 번째수]')
                    finally:
                        try:
                            await askmsg.delete()
                        except:
                            pass

                async def looper(canceltask, msgtask):
                    while True:
                        if canceltask.done():
                            msgtask.cancel()
                            return canceltask
                        elif msgtask.done():
                            canceltask.cancel()
                            return msgtask
                        await asyncio.sleep(0.1)

                if ctx.channel.last_message_id == msg.id:
                    await msg.edit(embed=await self.char_settings_embed(char, 'select'))
                else:
                    results = await asyncio.gather(
                        msg.delete(),
                        ctx.send(embed=await self.char_settings_embed(char, 'select'))
                    )
                    msg = results[1]
                    await addreaction(msg)
                    reaction.message = msg

                emj = reaction.emoji
                if emj == '✏':
                    editmsg = await ctx.send(embed=discord.Embed(title='⚙ 설정 변경 - 항목 선택', description='변경할 항목의 번째 수를 입력해주세요.\n또는 ❌ 버튼을 클릭해 취소할 수 있습니다.', color=self.color['ask']))
                    await editmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(wait_for_cancel(editmsg))
                    msgtask = asyncio.create_task(wait_for_setindex(editmsg))
                    rst = await looper(canceltask, msgtask)

                    if rst == msgtask and type(msgtask.result()) == int:
                        msgtask.result()

                    elif rst == msgtask and msgtask.result() == asyncio.TimeoutError:
                        embed = discord.Embed(title='⏰ 시간이 초과되었습니다!', color=self.color['info'])
                        embed.set_footer(text='이 메시지는 7초 후에 삭제됩니다.')
                        await ctx.send(embed=embed, delete_after=7)
                        self.msglog.log(ctx, '[가방: 시간 초과]')

                await asyncio.gather(
                    reaction.remove(user),
                    msg.edit(embed=await self.char_settings_embed(char))
                )

    @commands.command(name='스탯', aliases=['능력치'])
    async def _stat(self, ctx: commands.Context, charname: typing.Optional[str] = None):
        cmgr = CharMgr(self.cur)
        if not charname:
            char = cmgr.get_current_char(ctx.author.id)
        else:
            char = cmgr.get_character(charname)
        print(char.stat)
        await ctx.send(embed=discord.Embed(title=f'📊 `{char.name}` 의 능력치', description=str(char.stat), color=self.color['info']))
    
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

    @commands.command(name='낚시')
    async def _fishing(self, ctx: commands.Context):
        cmgr = CharMgr(self.cur)
        embed = discord.Embed(title='🎣 낚시', description='찌를 던졌습니다! 뭔가가 걸리면 재빨리 ⁉ 반응을 클릭하세요!', color=self.color['g-fishing'])
        msg = await ctx.send(embed=embed)
        await msg.edit()
        emjs = ['⁉']
        await msg.add_reaction('⁉')
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and str(reaction.emoji) in emjs

        async def do():
            todo = []
            if msg.id == ctx.channel.last_message_id:
                todo += [
                    msg.edit(embed=embed),
                    msg.clear_reactions()
                ]
            else:
                todo += [
                    msg.delete(),
                    ctx.send(embed=embed)
                ]
            await asyncio.gather(*todo, return_exceptions=True)

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=random.uniform(1, 5))
        except asyncio.TimeoutError:
            pass
        else:
            if reaction.emoji == '⁉':
                embed.description = '아무것도 잡히지 않았어요! 너무 빨리 당긴것 같아요.'
                await do()
                return
        embed.description = '뭔가가 걸렸습니다! 지금이에요!'
        await msg.edit(embed=embed)

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=random.uniform(0.8, 1.7))
        except asyncio.TimeoutError:
            embed.description = '놓쳐 버렸네요... 너무 천천히 당긴것 같아요.'
            await do()
        else:
            if reaction.emoji == '⁉':
                idgr = ItemDBMgr(self.datadb)
                fishes = idgr.fetch_items_with(tags=['fishing'])
                fish = random.choices(fishes, list(map(lambda x: x.meta['percentage'], fishes)))[0]
                imgr = ItemMgr(self.cur, cmgr.get_current_char(ctx.author.id).name)
                imgr.give_item(ItemData(fish.id, 1, []))
                embed.title += ' - 잡았습니다!'
                embed.description = '**`{}` 을(를)** 잡았습니다!'.format(fish.name)
                await do()

    @commands.command(name='돈받기', aliases=['돈줘', '돈내놔'])
    async def _getmoney(self, ctx: commands.Context):
        cmgr = CharMgr(self.cur)
        char = cmgr.get_current_char(ctx.author.id)
        rcv_money = cmgr.get_raw_character(char.name)['received_money']
        if self.cur.execute('select * from userdata where id=%s and type=%s', (ctx.author.id, 'Master')) != 0:
            pass
        elif rcv_money:
            await ctx.send(embed=discord.Embed(title='⏱ 오늘의 일일 기본금을 이미 받았습니다!', description='내일이 오면 다시 받을 수 있습니다.', color=self.color['info']))
            return
        imgr = ItemMgr(self.cur, cmgr.get_current_char(ctx.author.id).name)
        imgr.money += 1000
        self.cur.execute('update chardata set received_money=%s where name=%s', (True, char.name))
        await ctx.send(embed=discord.Embed(title='💸 일일 기본금을 받았습니다!', description='1000골드를 받았습니다.', color=self.color['info']))

    @commands.command(name='상점')
    async def _market(self, ctx: commands.Context):
        pass

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)