import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import typing
import re
import random
import json
from exts.utils import pager, emojibuttons, errors, timedelta, event_waiter
from exts.utils.basecog import BaseCog
from templates import errembeds, ingameembeds
from dateutil.relativedelta import relativedelta
from exts.utils.datamgr import CharMgr, ItemMgr, ItemDBMgr, CharacterType, CharacterData, ItemData, SettingData, Setting, SettingDBMgr, SettingMgr, MarketItem, MarketDBMgr, DataDB, RegionDBMgr

class InGamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            cmd.add_check(self.check.char_online)

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
        msg = await ctx.send(embed=await ingameembeds.backpack_embed(self, ctx, pgr, charname, 'default'))
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
                    if not ctx.channel.last_message or ctx.channel.last_message_id == msg.id:
                        await msg.edit(embed=await ingameembeds.backpack_embed(self, ctx, pgr, charname, 'select'))
                    else:
                        results = await asyncio.gather(
                            msg.delete(),
                            ctx.send(embed=await ingameembeds.backpack_embed(self, ctx, pgr, charname, 'select'))
                        )
                        msg = results[1]
                        await addreaction(msg)
                        reaction.message = msg

                if reaction.emoji == '❔':
                    # 아이템 정보 확인 섹션
                    itemidxmsg = await ctx.send(embed=discord.Embed(
                        title='🔍 아이템 정보 보기 - 아이템 선택',
                        description='자세한 정보를 확인할 아이템의 번째수를 입력해주세요.\n위 메시지에 아이템 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.',
                        color=self.color['ask']
                    ))
                    self.msglog.log(ctx, '[가방: 아이템 정보: 번째수 입력]')
                    await itemidxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=20))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=20))
                    
                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if idxtaskrst.content.isdecimal():
                            if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                                itemidx = int(idxtaskrst.content) - 1
                                infoitem = pgr.get_thispage()[itemidx]
                                embed = await ingameembeds.itemdata_embed(self.datadb, ctx, infoitem)
                                embed.set_footer(text='❌ 버튼을 클릭해 이 메시지를 닫습니다.')
                                iteminfomsg = await ctx.send(embed=embed)
                                self.msglog.log(ctx, '[가방: 아이템 정보]')
                                await iteminfomsg.add_reaction('❌')
                                await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=iteminfomsg, emojis=['❌'], timeout=60*5)
                                await iteminfomsg.delete()
                            else:
                                embed = discord.Embed(title='❓ 아이템 번째수가 올바르지 않습니다!', description='위 메시지에 아이템 앞마다 번호가 붙어 있습니다.', color=self.color['error'])
                                embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[가방: 아이템 정보: 올바르지 않은 번째수]')
                        else:
                            embed = discord.Embed(title='❓ 아이템 번째수는 숫자만을 입력해주세요!', color=self.color['error'])
                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                            await ctx.send(embed=embed, delete_after=7)
                            self.msglog.log(ctx, '[가방: 아이템 정보: 숫자만 입력]')

                elif reaction.emoji == '🗑' and owner:
                    itemidxmsg = await ctx.send(embed=discord.Embed(
                        title='📮 아이템 버리기 - 아이템 선택',
                        description='버릴 아이템의 번째수를 입력해주세요.\n위 메시지에 아이템 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.',
                        color=self.color['ask']
                    ))
                    self.msglog.log(ctx, '[가방: 아이템 버리기: 번째수 입력]')
                    await itemidxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=20))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=20))

                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if idxtaskrst.content.isdecimal():
                            if int(idxtaskrst.content) <= len(pgr.pages()):
                                itemidx = int(idxtaskrst.content) - 1
                                delitem = pgr.get_thispage()[itemidx]
                                delcountmsg = await ctx.send(embed=discord.Embed(
                                    title='📮 아이템 버리기 - 아이템 개수',
                                    description=f'버릴 개수를 입력해주세요. **(현재 {delitem.count}개)**\n❌를 클릭해 취소합니다.',
                                    color=self.color['ask']
                                ))
                                self.msglog.log(ctx, '[가방: 아이템 버리기: 개수 입력]')
                                await delcountmsg.add_reaction('❌')
                                canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=delcountmsg, emojis=['❌'], timeout=20))
                                counttask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=20))
                                task = await event_waiter.wait_for_first(canceltask, counttask)
                                await delcountmsg.delete()
                                if task == counttask:
                                    countmsg = counttask.result()
                                    if countmsg.content.isdecimal():
                                        delcount = int(countmsg.content)
                                        if 1 <= delcount <= delitem.count:
                                            embed = await ingameembeds.itemdata_embed(self.datadb, ctx, delitem, 'delete', delete_count=delcount)
                                            deloxmsg = await ctx.send(embed=embed)
                                            self.msglog.log(ctx, '[가방: 아이템 버리기: 아이템 삭제 경고]')
                                            oxemjs = [self.emj.get(ctx, 'check'), self.emj.get(ctx, 'cross')]
                                            for em in oxemjs:
                                                await deloxmsg.add_reaction(em)
                                            rst = await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=deloxmsg, emojis=oxemjs, timeout=30)
                                            await deloxmsg.delete()
                                            if rst:
                                                if rst[0].emoji == self.emj.get(ctx, 'check'):
                                                    imgr.delete_item(delitem, delcount)
                                                    embed = discord.Embed(title='{} 아이템을 버렸습니다!'.format(self.emj.get(ctx, 'check')), color=self.color['success'])
                                                    embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                                    await ctx.send(embed=embed, delete_after=7)
                                                    self.msglog.log(ctx, '[가방: 아이템 버리기: 완료]')

                                        else:
                                            embed = discord.Embed(title='❓ 버릴 아이템 개수가 올바르지 않습니다!', color=self.color['error'])
                                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                            await ctx.send(embed=embed, delete_after=7)
                                            self.msglog.log(ctx, '[가방: 아이템 버리기: 올바르지 않은 개수]')
                                    else:
                                        embed = discord.Embed(title='❓ 아이템 개수는 숫자만을 입력해주세요!', color=self.color['error'])
                                        embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                        await ctx.send(embed=embed, delete_after=7)
                                        self.msglog.log(ctx, '[가방: 아이템 버리기: 숫자만 입력]')
                            else:
                                embed = discord.Embed(title='❓ 아이템 번째수가 올바르지 않습니다!', description='위 메시지에 아이템 앞마다 번호가 붙어 있습니다.', color=self.color['error'])
                                embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[가방: 아이템 버리기: 올바르지 않은 번째수]')
                        else:
                            embed = discord.Embed(title='❓ 아이템 번째수는 숫자만을 입력해주세요!', color=self.color['error'])
                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                            await ctx.send(embed=embed, delete_after=7)
                            self.msglog.log(ctx, '[가방: 아이템 버리기: 숫자만 입력]')
                    
                pgr.set_obj(imgr.get_items())
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                await asyncio.gather(do,
                    msg.edit(embed=await ingameembeds.backpack_embed(self, ctx, pgr, charname, 'default')),
                )

    @commands.command(name='상점')
    async def _market(self, ctx: commands.Context):
        perpage = 8
        mdgr = MarketDBMgr(self.datadb)
        pgr = pager.Pager(mdgr.get_market('main'), perpage)
        msg = await ctx.send(embed=await ingameembeds.market_embed(self.datadb, pgr, color=self.color['info']))
        self.msglog.log(ctx, '[상점]')
        extemjs = ['💎', '💰', '❔']
        if len(pgr.pages()) <= 1:
            emjs = extemjs
        else:
            emjs = emojibuttons.PageButton.emojis + extemjs
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
                if reaction.emoji in extemjs:
                    if not ctx.channel.last_message or ctx.channel.last_message_id == msg.id:
                        await msg.edit(embed=await ingameembeds.market_embed(self.datadb, pgr, color=self.color['info'], mode='select'))
                    else:
                        results = await asyncio.gather(
                            msg.delete(),
                            ctx.send(embed=await ingameembeds.market_embed(self.datadb, pgr, color=self.color['info'], mode='select'))
                        )
                        msg = results[1]
                        await addreaction(msg)
                        reaction.message = msg
                if reaction.emoji == '💎':
                    pass
                elif reaction.emoji == '💰':
                    pass
                elif reaction.emoji == '❔':
                    # 상점아이템 정보 확인 섹션
                    itemidxmsg = await ctx.send(embed=discord.Embed(
                        title='🔍 아이템 정보 보기 - 아이템 선택',
                        description='자세한 정보를 확인할 아이템의 번째수를 입력해주세요.\n위 메시지에 아이템 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.',
                        color=self.color['ask']
                    ))
                    self.msglog.log(ctx, '[상점: 아이템 정보: 번째수 입력]')
                    await itemidxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=20))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=20))
                    
                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if idxtaskrst.content.isdecimal():
                            if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                                itemidx = int(idxtaskrst.content) - 1
                                infoitem = pgr.get_thispage()[itemidx]
                                embed = await ingameembeds.marketitem_embed(self.datadb, ctx, infoitem)
                                embed.set_footer(text='❌ 버튼을 클릭해 이 메시지를 닫습니다.')
                                iteminfomsg = await ctx.send(embed=embed)
                                self.msglog.log(ctx, '[상점: 아이템 정보]')
                                await iteminfomsg.add_reaction('❌')
                                await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=iteminfomsg, emojis=['❌'], timeout=60*5)
                                await iteminfomsg.delete()
                            else:
                                embed = discord.Embed(title='❓ 아이템 번째수가 올바르지 않습니다!', description='위 메시지에 아이템 앞마다 번호가 붙어 있습니다.', color=self.color['error'])
                                embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[상점: 아이템 정보: 올바르지 않은 번째수]')
                        else:
                            embed = discord.Embed(title='❓ 아이템 번째수는 숫자만을 입력해주세요!', color=self.color['error'])
                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                            await ctx.send(embed=embed, delete_after=7)
                            self.msglog.log(ctx, '[상점: 아이템 정보: 숫자만 입력]')

                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                if asyncio.iscoroutine(do):
                    await asyncio.gather(do,
                        msg.edit(embed=await ingameembeds.market_embed(self.datadb, pgr, color=self.color['info'])),
                    )

    async def char_settings_embed(self, char: CharacterData, mode='default'):
        sdgr = SettingDBMgr(self.datadb)
        smgr = SettingMgr(self.cur, sdgr, char)
        settitles = []
        setvalue = []
        for idx in range(len(self.datadb.char_settings)):
            st = self.datadb.char_settings[idx]
            settitles.append(st.title)
            valuestr = str(smgr.get_setting(st.name))
            for x in [('True', '켜짐'), ('False', '꺼짐')]:
                valuestr = valuestr.replace(x[0], x[1])
            setvalue.append(valuestr)
        embed = discord.Embed(title='⚙ `{}` 캐릭터 설정'.format(char.name), color=self.color['info'])
        if mode == 'select':
            embed.title += ' - 선택 모드'
            embed.add_field(name='번호', value='\n'.join(map(str, range(1, len(self.datadb.char_settings)+1))))
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
                            if 1 <= idx <= len(self.datadb.char_settings):
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
        now = datetime.datetime.now()
        embed = discord.Embed(title='💸 일일 기본금을 받았습니다!', description='1000골드를 받았습니다.', color=self.color['info'])
        if self.cur.execute('select * from userdata where id=%s and type=%s', (ctx.author.id, 'Master')) != 0:
            embed.description += '\n관리자여서 돈을 무제한으로 받을 수 있습니다. 멋지네요!'
        elif now.day <= rcv_money.day:
            await ctx.send(ctx.author.mention, embed=discord.Embed(title='⏱ 오늘의 일일 기본금을 이미 받았습니다!', description='내일이 오면 다시 받을 수 있습니다.', color=self.color['info']))
            return
        imgr = ItemMgr(self.cur, cmgr.get_current_char(ctx.author.id).name)
        imgr.money += 1000
        self.cur.execute('update chardata set received_money=%s where name=%s', (now, char.name))
        await ctx.send(ctx.author.mention, embed=embed)

    @commands.command(name='지도', aliases=['내위치', '위치', '현재위치', '맵'])
    async def _map(self, ctx: commands.Context):
        cmgr = CharMgr(self.cur)
        char = cmgr.get_current_char(ctx.author.id)
        rdgr = RegionDBMgr(self.datadb)
        rgn = rdgr.get_warpables('azalea')
        embed = discord.Embed(title='🗺 지도', description='', color=self.color['info'])
        for one in rgn:
            if char.location.name == one.name:
                embed.description += '{} **{} (현재)** 🔸 \n'.format(one.icon, one.title)
            else:
                embed.description += '{} {}\n'.format(one.icon, one.title)
        await ctx.send(embed=embed)

    @commands.command(name='이동', aliases=['워프'])
    async def _warp(self, ctx: commands.Context):
        cmgr = CharMgr(self.cur)
        char = cmgr.get_current_char(ctx.author.id)
        rdgr = RegionDBMgr(self.datadb)
        rgn = rdgr.get_warpables('azalea')
        rgn = list(filter(lambda x: x.name != char.location.name, rgn))
        now = rdgr.get_region('azalea', char.location.name)
        print(now)
        embed = discord.Embed(title='✈ 이동', description='이동할 위치를 선택하세요!\n**현재 위치: {}**\n\n'.format(now.icon + ' ' + now.title), color=self.color['ask'])
        for one in rgn:
            embed.description += f'{one.icon} {one.title}\n'
        msg = await ctx.send(embed=embed)
        emjs = []
        for em in rgn:
            emjs.append(em.icon)
            await msg.add_reaction(em.icon)
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
            idx = emjs.index(reaction.emoji)
            region = rgn[idx]
            cmgr.move_to(char.name, region)
            await ctx.send(embed=discord.Embed(title='{} `{}` 으(로) 이동했습니다!'.format(region.icon, region.title), color=self.color['success']))

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)