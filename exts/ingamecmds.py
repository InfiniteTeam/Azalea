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
from exts.utils.datamgr import (
    CharMgr, ItemMgr, ItemDBMgr, CharacterType, CharacterData, ItemData, 
    SettingData, Setting, SettingDBMgr, SettingMgr, MarketItem, MarketDBMgr, DataDB, RegionDBMgr
)

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
            if len(pgr.pages()) == 0:
                return
            elif len(pgr.pages()) <= 1:
                for emj in extemjs:
                    await m.add_reaction(emj)
            else:
                for emj in emjs:
                    await m.add_reaction(emj)
        await addreaction(msg)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
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
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60))
                    
                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if idxtaskrst.content.isdecimal():
                            if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                                itemidx = int(idxtaskrst.content) - 1
                                infoitem = pgr.get_thispage()[itemidx]
                                embed = await ingameembeds.itemdata_embed(self, infoitem)
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
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60))

                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if idxtaskrst.content.isdecimal():
                            if int(idxtaskrst.content) <= len(pgr.get_thispage()):
                                itemidx = int(idxtaskrst.content) - 1
                                delitem = pgr.get_thispage()[itemidx]
                                delcountmsg = await ctx.send(embed=discord.Embed(
                                    title='📮 아이템 버리기 - 아이템 개수',
                                    description=f'버릴 개수를 입력해주세요. **(현재 {delitem.count}개)**\n❌를 클릭해 취소합니다.',
                                    color=self.color['ask']
                                ))
                                self.msglog.log(ctx, '[가방: 아이템 버리기: 개수 입력]')
                                await delcountmsg.add_reaction('❌')
                                canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=delcountmsg, emojis=['❌'], timeout=60))
                                counttask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60))
                                task = await event_waiter.wait_for_first(canceltask, counttask)
                                await delcountmsg.delete()
                                if task == counttask:
                                    countmsg = counttask.result()
                                    if countmsg.content.isdecimal():
                                        delcount = int(countmsg.content)
                                        if 1 <= delcount <= delitem.count:
                                            embed = await ingameembeds.itemdata_embed(self, delitem, 'delete', count=delcount)
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
        cmgr = CharMgr(self.cur)
        char = cmgr.get_current_char(ctx.author.id)
        idgr = ItemDBMgr(self.datadb)
        imgr = ItemMgr(self.cur, char.name)
        mkt = mdgr.get_market('main')
        pgr = pager.Pager(mkt, perpage)
        msg = await ctx.send(embed=await ingameembeds.market_embed(self.datadb, pgr, color=self.color['info']))
        self.msglog.log(ctx, '[상점]')
        extemjs = ['💎', '💰', '❔']
        if len(pgr.pages()) == 0:
            return
        elif len(pgr.pages()) <= 1:
            emjs = extemjs
        else:
            emjs = emojibuttons.PageButton.emojis + extemjs
        async def addreaction(msg):
            for em in emjs:
                await msg.add_reaction(em)
        await addreaction(msg)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except:
                    pass
            else:
                if reaction.emoji in ['💎']:
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
                elif reaction.emoji in ['💰']:
                    can_sell = list(filter(lambda x: idgr.fetch_item(x.id).selling is not None, imgr.get_items()))
                    pgr2 = pager.Pager(can_sell, perpage=8)
                    if not ctx.channel.last_message or ctx.channel.last_message_id == msg.id:
                        await msg.edit(embed=await ingameembeds.backpack_sell_embed(self, ctx, pgr2, char.name))
                    else:
                        results = await asyncio.gather(
                            msg.delete(),
                            ctx.send(embed=await ingameembeds.backpack_sell_embed(self, ctx, pgr2, char.name))
                        )
                        msg = results[1]
                        await addreaction(msg)
                        reaction.message = msg

                if reaction.emoji == '💰':
                    # 상점아이템 판매 섹션
                    if len(pgr2.pages()) == 0:
                        await ctx.send(embed=discord.Embed(title='📦 판매할 수 있는 아이템이 하나도 없습니다!', color=self.color['error']))
                    else:
                        itemidxmsg = await ctx.send(embed=discord.Embed(
                            title='💰 아이템 판매 - 아이템 선택',
                            description='판매할 아이템의 번째수를 입력해주세요.\n위 메시지에 아이템 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.',
                            color=self.color['ask']
                        ))
                        self.msglog.log(ctx, '[상점: 아이템 판매: 번째수 입력]')
                        await itemidxmsg.add_reaction('❌')
                        canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                        indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60))
                        task = await event_waiter.wait_for_first(canceltask, indextask)
                        await itemidxmsg.delete()

                        if task == indextask:
                            idxtaskrst = indextask.result()
                            if idxtaskrst.content.isdecimal():
                                if 1 <= int(idxtaskrst.content) <= len(pgr2.get_thispage()):
                                    itemidx = int(idxtaskrst.content) - 1
                                    item: ItemData = pgr2.get_thispage()[itemidx]
                                    itemcountmsg = await ctx.send(embed=discord.Embed(
                                        title='💰 아이템 판매 - 판매 아이템 개수',
                                        description='몇 개를 판매하시겠어요? (최대 {}개)\n❌를 클릭해 취소합니다.'.format(item.count),
                                        color=self.color['ask']
                                    ))
                                    self.msglog.log(ctx, '[상점: 아이템 판매: 개수 입력]')
                                    await itemcountmsg.add_reaction('❌')
                                    canceltask2 = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemcountmsg, emojis=['❌'], timeout=60))
                                    counttask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60))
                                    task2 = await event_waiter.wait_for_first(canceltask2, counttask)
                                    await itemcountmsg.delete()
                                    if task2 == counttask:
                                        counttaskrst = counttask.result()
                                        if counttaskrst.content.isdecimal():
                                            count = int(counttaskrst.content)
                                            if count >= 1:
                                                if count <= item.count:
                                                    embed = await ingameembeds.itemdata_embed(self, item, 'sell', count=count, chardata=char)
                                                    finalmsg = await ctx.send(embed=embed)
                                                    await finalmsg.add_reaction('⭕')
                                                    await finalmsg.add_reaction('❌')
                                                    rst = await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=finalmsg, emojis=['⭕', '❌'], timeout=60)
                                                    if rst:
                                                        rct = rst[0]
                                                        if rct.emoji == '⭕':
                                                            #판매 전 최종 확인
                                                            if item in imgr.get_items():
                                                                imgr.delete_item(item, count)
                                                                final_price = idgr.get_final_price(item, count)
                                                                imgr.money += final_price
                                                                await ctx.send(embed=discord.Embed(
                                                                    title='{} 성공적으로 판매했습니다!'.format(self.emj.get(ctx, 'check')),
                                                                    description='{} 을(를) {} 개 판매했어요.'.format(idgr.fetch_item(item.id).name, count),
                                                                    color=self.color['success']
                                                                ))
                                                                self.msglog.log(ctx, '[상점: 아이템 판매: 완료]')
                                                            else:
                                                                embed = discord.Embed(title='❓ 해당 아이템을 찾을 수 없습니다!', description='아이템을 이미 판매했거나, 버렸지는 않은가요?', color=self.color['error'])
                                                                embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                                                await ctx.send(embed=embed, delete_after=7)
                                                                self.msglog.log(ctx, '[상점: 아이템 판매: 아이템 찾을 수 없음]')
                                                        elif rct.emoji == '❌':
                                                            embed = discord.Embed(title='❌ 취소되었습니다.', color=self.color['error'])
                                                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                                            await ctx.send(embed=embed, delete_after=7)
                                                            self.msglog.log(ctx, '[상점: 아이템 판매: 취소]')
                                                    await finalmsg.delete()
                                                else:
                                                    embed = discord.Embed(title='❌ 판매하려는 양이 너무 많습니다!', description='이 아이템은 최대 {}개를 판매할 수 있습니다.'.format(item.count), color=self.color['error'])
                                                    embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                                    await ctx.send(embed=embed, delete_after=7)
                                                    self.msglog.log(ctx, '[상점: 아이템 판매: 아이템 부족]')
                                            else:
                                                embed = discord.Embed(title='❓ 아이템 개수는 적어도 1개 이상이여야 합니다!', color=self.color['error'])
                                                embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                                await ctx.send(embed=embed, delete_after=7)
                                                self.msglog.log(ctx, '[상점: 아이템 판매: 1 이상이여야 함]')
                                        else:
                                            embed = discord.Embed(title='❓ 아이템 개수는 숫자만을 입력해주세요!', color=self.color['error'])
                                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                            await ctx.send(embed=embed, delete_after=7)
                                            self.msglog.log(ctx, '[상점: 아이템 판매: 숫자만 입력]')
                                else:
                                    embed = discord.Embed(title='❓ 아이템 번째수가 올바르지 않습니다!', description='위 메시지에 아이템 앞마다 번호가 붙어 있습니다.', color=self.color['error'])
                                    embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                    await ctx.send(embed=embed, delete_after=7)
                                    self.msglog.log(ctx, '[상점: 아이템 판매: 올바르지 않은 번째수]')
                            else:
                                embed = discord.Embed(title='❓ 아이템 번째수는 숫자만을 입력해주세요!', color=self.color['error'])
                                embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[상점: 아이템 판매: 숫자만 입력]')

                elif reaction.emoji == '💎':
                    # 상점아이템 구매 섹션
                    itemidxmsg = await ctx.send(embed=discord.Embed(
                        title='💎 아이템 구매 - 아이템 선택',
                        description='구매할 아이템의 번째수를 입력해주세요.\n위 메시지에 아이템 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.',
                        color=self.color['ask']
                    ))
                    self.msglog.log(ctx, '[상점: 아이템 구매: 번째수 입력]')
                    await itemidxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60))

                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if idxtaskrst.content.isdecimal():
                            if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                                itemidx = int(idxtaskrst.content) - 1
                                item: MarketItem = pgr.get_thispage()[itemidx]
                                itemcountmsg = await ctx.send(embed=discord.Embed(
                                    title='💎 아이템 구매 - 구매 아이템 개수',
                                    description='몇 개를 구매하시겠어요?\n❌를 클릭해 취소합니다.',
                                    color=self.color['ask']
                                ))
                                self.msglog.log(ctx, '[상점: 아이템 구매: 개수 입력]')
                                await itemcountmsg.add_reaction('❌')
                                canceltask2 = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemcountmsg, emojis=['❌'], timeout=60))
                                counttask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60))
                                task2 = await event_waiter.wait_for_first(canceltask2, counttask)
                                await itemcountmsg.delete()
                                if task2 == counttask:
                                    counttaskrst = counttask.result()
                                    if counttaskrst.content.isdecimal():
                                        count = int(counttaskrst.content)
                                        if item.discount:
                                            final_price = count * item.discount
                                        else:
                                            final_price = count * item.price

                                        char = cmgr.get_current_char(ctx.author.id)
                                        if count >= 1:
                                            if final_price <= char.money:
                                                # 최종적 구매 확인
                                                embed = await ingameembeds.marketitem_embed(self, item, mode='buy', chardata=char, count=count)
                                                finalmsg = await ctx.send(embed=embed)
                                                await finalmsg.add_reaction('⭕')
                                                await finalmsg.add_reaction('❌')
                                                rst = await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=finalmsg, emojis=['⭕', '❌'], timeout=60)
                                                if rst:
                                                    rct = rst[0]
                                                    if rct.emoji == '⭕':
                                                        # 캐릭터 갱신 후 다시 한번 잔고 충분한지 확인
                                                        char = cmgr.get_current_char(ctx.author.id)
                                                        if final_price <= char.money:
                                                            imgr = ItemMgr(self.cur, char.name)
                                                            imgr.money -= final_price
                                                            item.item.count = count
                                                            imgr.give_item(item.item)

                                                            embed = discord.Embed(title='{} 성공적으로 구매했습니다!'.format(self.emj.get(ctx, 'check')), description='`{}` 을(를) {}개 구입했어요.'.format(idgr.fetch_item(item.item.id).name, count), color=self.color['success'])
                                                            await ctx.send(embed=embed)
                                                            self.msglog.log(ctx, '[상점: 아이템 구매: 완료]')
                                                        else:
                                                            embed = discord.Embed(title='❓ 구매에 필요한 돈이 부족합니다!', description='`{}`골드가 부족합니다!'.format(final_price - char.money), color=self.color['error'])
                                                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                                            await ctx.send(embed=embed, delete_after=7)
                                                            self.msglog.log(ctx, '[상점: 아이템 구매: 돈 부족]')
                                                    elif rct.emoji == '❌':
                                                        embed = discord.Embed(title='❌ 취소되었습니다.', color=self.color['error'])
                                                        embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                                        await ctx.send(embed=embed, delete_after=7)
                                                        self.msglog.log(ctx, '[상점: 아이템 구매: 취소]')
                                                await finalmsg.delete()
                                            else:
                                                #돈 부족
                                                embed = discord.Embed(title='❓ 구매에 필요한 돈이 부족합니다!', description='`{}`골드가 부족합니다!'.format(final_price - char.money), color=self.color['error'])
                                                embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                                await ctx.send(embed=embed, delete_after=7)
                                                self.msglog.log(ctx, '[상점: 아이템 구매: 돈 부족]')
                                        else:
                                            embed = discord.Embed(title='❓ 아이템 개수는 적어도 1개 이상이여야 합니다!', color=self.color['error'])
                                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                            await ctx.send(embed=embed, delete_after=7)
                                            self.msglog.log(ctx, '[상점: 아이템 구매: 1 이상이여야 함]')
                                    else:
                                        embed = discord.Embed(title='❓ 아이템 개수는 숫자만을 입력해주세요!', color=self.color['error'])
                                        embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                        await ctx.send(embed=embed, delete_after=7)
                                        self.msglog.log(ctx, '[상점: 아이템 구매: 숫자만 입력]')
                            else:
                                embed = discord.Embed(title='❓ 아이템 번째수가 올바르지 않습니다!', description='위 메시지에 아이템 앞마다 번호가 붙어 있습니다.', color=self.color['error'])
                                embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[상점: 아이템 구매: 올바르지 않은 번째수]')
                        else:
                            embed = discord.Embed(title='❓ 아이템 번째수는 숫자만을 입력해주세요!', color=self.color['error'])
                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                            await ctx.send(embed=embed, delete_after=7)
                            self.msglog.log(ctx, '[상점: 아이템 구매: 숫자만 입력]')

                elif reaction.emoji == '❔':
                    # 상점아이템 정보 확인 섹션
                    itemidxmsg = await ctx.send(embed=discord.Embed(
                        title='🔍 아이템 정보 보기 - 아이템 선택',
                        description='자세한 정보를 확인할 아이템의 번째수를 입력해주세요.\n위 메시지에 아이템 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.',
                        color=self.color['ask']
                    ))
                    self.msglog.log(ctx, '[상점: 아이템 정보: 번째수 입력]')
                    await itemidxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60))
                    
                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if idxtaskrst.content.isdecimal():
                            if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                                itemidx = int(idxtaskrst.content) - 1
                                infoitem = pgr.get_thispage()[itemidx]
                                embed = await ingameembeds.marketitem_embed(self, infoitem)
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

    @commands.command(name='스탯', aliases=['능력치'])
    async def _stat(self, ctx: commands.Context, charname: typing.Optional[str] = None):
        cmgr = CharMgr(self.cur)
        if not charname:
            char = cmgr.get_current_char(ctx.author.id)
        else:
            char = cmgr.get_character(charname)
        embed = discord.Embed(title=f'📊 `{char.name}` 의 정보', color=self.color['info'])
        embed.add_field(name='기본 정보', value=f'**레벨:** `{char.level}`')
        embed.add_field(name='능력치', value=f'{char.stat}')
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[스탯]')

    @commands.command(name='돈받기', aliases=['돈줘', '돈내놔', '출첵', '출석'])
    async def _getmoney(self, ctx: commands.Context):
        cmgr = CharMgr(self.cur)
        char = cmgr.get_current_char(ctx.author.id)
        rcv_money = cmgr.get_raw_character(char.name)['received_money']
        now = datetime.datetime.now()
        embed = discord.Embed(title='💸 일일 기본금을 받았습니다!', description='1000골드를 받았습니다.', color=self.color['info'])
        if self.cur.execute('select * from userdata where id=%s and type=%s', (ctx.author.id, 'Master')) != 0:
            embed.description += '\n관리자여서 돈을 무제한으로 받을 수 있습니다. 멋지네요!'
        elif rcv_money is None:
            pass
        elif now.day <= rcv_money.day:
            await ctx.send(ctx.author.mention, embed=discord.Embed(title='⏱ 오늘의 일일 기본금을 이미 받았습니다!', description='내일이 오면 다시 받을 수 있습니다.', color=self.color['info']))
            self.msglog.log(ctx, '[돈받기: 이미 받음]')
            return
        imgr = ItemMgr(self.cur, cmgr.get_current_char(ctx.author.id).name)
        imgr.money += 1000
        self.cur.execute('update chardata set received_money=%s where name=%s', (now, char.name))
        await ctx.send(ctx.author.mention, embed=embed)
        self.msglog.log(ctx, '[돈받기: 완료]')

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
        self.msglog.log(ctx, '[지도]')

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
        self.msglog.log(ctx, '[이동]')
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
            self.msglog.log(ctx, '[이동: 완료]')

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)