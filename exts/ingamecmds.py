import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import aiomysql
import typing
import math
from utils import pager, emojibuttons, event_waiter, progressbar, mgrerrors
from utils.basecog import BaseCog
from utils.datamgr import (
    CharMgr, ItemMgr, ItemDBMgr, ItemData, StatType, StatMgr,
    SettingDBMgr, SettingMgr, MarketItem, MarketDBMgr, RegionDBMgr, ExpTableDBMgr, MarketMgr
)

class InGamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            cmd.add_check(self.check.char_online)

    @commands.command(name='돈', aliases=['내돈', '지갑'])
    async def _money(self, ctx: commands.Context, *, charname: typing.Optional[str]=None):
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname)
            if not char:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', charname))
                self.msglog.log(ctx, '[가방: 존재하지 않는 캐릭터]')
                return
        else:
            char = await cmgr.get_current_char(ctx.author.id)

        await ctx.send(embed=await self.embedmgr.get(ctx, 'Wallet', char))

    @commands.command(name='가방', aliases=['템', '아이템'])
    @commands.guild_only()
    async def _backpack(self, ctx: commands.Context, *, charname: typing.Optional[str]=None):
        perpage = 8
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname)
            if char:
                imgr = ItemMgr(self.pool, char.uid)
            else:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', charname))
                self.msglog.log(ctx, '[가방: 존재하지 않는 캐릭터]')
                return
        else:
            char = await cmgr.get_current_char(ctx.author.id)
            charname = char.name
            imgr = ItemMgr(self.pool, char.uid)

        sdgr = SettingDBMgr(self.datadb)
        smgr = SettingMgr(self.pool, sdgr, char.uid)

        if char.id != ctx.author.id and await smgr.get_setting('private-item'):
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Items_private'))
            return
        
        items = await imgr.get_items()
        
        pgr = pager.Pager(items, perpage=perpage)
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Backpack', pgr, char.uid))
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
                        await msg.edit(embed=await self.embedmgr.get(ctx, 'Backpack', pgr, char.uid, mode='select'))
                    else:
                        results = await asyncio.gather(
                            msg.delete(),
                            ctx.send(embed=await self.embedmgr.get(ctx, 'Backpack', pgr, char.uid, mode='select'))
                        )
                        msg = results[1]
                        await addreaction(msg)
                        reaction.message = msg

                if reaction.emoji == '❔':
                    # 아이템 정보 확인 섹션
                    itemidxmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Item_info_select_index'))
                    self.msglog.log(ctx, '[가방: 아이템 정보: 번째수 입력]')
                    await itemidxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))
                    
                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                            itemidx = int(idxtaskrst.content) - 1
                            infoitem = pgr.get_thispage()[itemidx]
                            embed = await self.embedmgr.get(ctx, 'Item_info', infoitem, xtoclose=True)
                            iteminfomsg = await ctx.send(embed=embed)
                            self.msglog.log(ctx, '[가방: 아이템 정보]')
                            await iteminfomsg.add_reaction('❌')
                            await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=iteminfomsg, emojis=['❌'], timeout=60*5)
                            await iteminfomsg.delete()
                        else:
                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Invalid_item_index', delafter=7), delete_after=7)
                            self.msglog.log(ctx, '[가방: 아이템 정보: 올바르지 않은 번째수]')

                elif reaction.emoji == '🗑' and owner:
                    itemidxmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Item_discard_select_index'))
                    self.msglog.log(ctx, '[가방: 아이템 버리기: 번째수 입력]')
                    await itemidxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))

                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if int(idxtaskrst.content) <= len(pgr.get_thispage()):
                            itemidx = int(idxtaskrst.content) - 1
                            delitem = pgr.get_thispage()[itemidx]
                            delcountmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Item_discard_count', delitem))
                            self.msglog.log(ctx, '[가방: 아이템 버리기: 개수 입력]')
                            await delcountmsg.add_reaction('❌')
                            canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=delcountmsg, emojis=['❌'], timeout=60))
                            counttask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))
                            task = await event_waiter.wait_for_first(canceltask, counttask)
                            await delcountmsg.delete()
                            if task == counttask:
                                countmsg = counttask.result()
                                delcount = int(countmsg.content)
                                if 1 <= delcount <= delitem.count:
                                    embed = await self.embedmgr.get(ctx, 'Item_info', delitem, mode='delete', count=delcount)
                                    deloxmsg = await ctx.send(embed=embed)
                                    self.msglog.log(ctx, '[가방: 아이템 버리기: 아이템 삭제 경고]')
                                    oxemjs = [self.emj.get(ctx, 'check'), self.emj.get(ctx, 'cross')]
                                    for em in oxemjs:
                                        await deloxmsg.add_reaction(em)
                                    rst = await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=deloxmsg, emojis=oxemjs, timeout=30)
                                    await deloxmsg.delete()
                                    if rst:
                                        if rst[0].emoji == self.emj.get(ctx, 'check'):
                                            await imgr.delete_item(delitem, delcount)
                                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Item_discard_done', delafter=7), delete_after=7)
                                            self.msglog.log(ctx, '[가방: 아이템 버리기: 완료]')
                                else:
                                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Item_discard_invalid_count', delafter=7), delete_after=7)
                                    self.msglog.log(ctx, '[가방: 아이템 버리기: 올바르지 않은 개수]')
                        else:
                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Invalid_item_index', delafter=7), delete_after=7)
                            self.msglog.log(ctx, '[가방: 아이템 버리기: 올바르지 않은 번째수]')
                    
                pgr.set_obj(await imgr.get_items())
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                await asyncio.gather(do,
                    msg.edit(embed=await self.embedmgr.get(ctx, 'Backpack', pgr, char.uid)),
                )

    @commands.command(name='상점', aliases=['샵', '가게', '마트', '시장', '쇼핑', '마켓'])
    async def _market(self, ctx: commands.Context):
        perpage = 8
        mdgr = MarketDBMgr(self.datadb)
        cmgr = CharMgr(self.pool)
        char = await cmgr.get_current_char(ctx.author.id)
        idgr = ItemDBMgr(self.datadb)
        imgr = ItemMgr(self.pool, char.uid)
        mmgr = MarketMgr(self.pool, self.datadb, char.uid)
        mkt = mdgr.get_market('main')
        pgr = pager.Pager(mkt, perpage)
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Market', pgr))
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
                if reaction.emoji in ['💎', '❔']:
                    if not ctx.channel.last_message or ctx.channel.last_message_id == msg.id:
                        await msg.edit(embed=await self.embedmgr.get(ctx, 'Market', pgr, mode='select'))
                    else:
                        results = await asyncio.gather(
                            msg.delete(),
                            ctx.send(embed=await self.embedmgr.get(ctx, 'Market', pgr, mode='select'))
                        )
                        msg = results[1]
                        await addreaction(msg)
                        reaction.message = msg
                elif reaction.emoji in ['💰']:
                    can_sell = list(filter(lambda x: idgr.fetch_item(x.id).selling is not None, await imgr.get_items()))
                    pgr2 = pager.Pager(can_sell, perpage=8)
                    if not ctx.channel.last_message or ctx.channel.last_message_id == msg.id:
                        await msg.edit(embed=await self.embedmgr.get(ctx, 'Backpack_sell', pgr2, char))
                    else:
                        results = await asyncio.gather(
                            msg.delete(),
                            ctx.send(embed=await self.embedmgr.get(ctx, 'Backpack_sell', pgr2, char))
                        )
                        msg = results[1]
                        await addreaction(msg)
                        reaction.message = msg

                if reaction.emoji == '💰':
                    # 상점아이템 판매 섹션
                    if len(pgr2.pages()) == 0:
                        await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_sell_no_any'))
                    else:
                        itemidxmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_sell_select_item'))
                        self.msglog.log(ctx, '[상점: 아이템 판매: 번째수 입력]')
                        await itemidxmsg.add_reaction('❌')
                        canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                        indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))
                        task = await event_waiter.wait_for_first(canceltask, indextask)
                        await itemidxmsg.delete()

                        if task == indextask:
                            idxtaskrst = indextask.result()
                            if 1 <= int(idxtaskrst.content) <= len(pgr2.get_thispage()):
                                itemidx = int(idxtaskrst.content) - 1
                                item: ItemData = pgr2.get_thispage()[itemidx]
                                itemcountmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_sell_count', item))
                                self.msglog.log(ctx, '[상점: 아이템 판매: 개수 입력]')
                                await itemcountmsg.add_reaction('❌')
                                canceltask2 = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemcountmsg, emojis=['❌'], timeout=60))
                                counttask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))
                                task2 = await event_waiter.wait_for_first(canceltask2, counttask)
                                await itemcountmsg.delete()
                                if task2 == counttask:
                                    counttaskrst = counttask.result()
                                    count = int(counttaskrst.content)
                                    if count >= 1:
                                        if count <= item.count:
                                            embed = await self.embedmgr.get(ctx, 'Item_info', item, mode='sell', count=count, charuuid=char.uid)
                                            finalmsg = await ctx.send(embed=embed)
                                            await finalmsg.add_reaction('⭕')
                                            await finalmsg.add_reaction('❌')
                                            rst = await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=finalmsg, emojis=['⭕', '❌'], timeout=60)
                                            if rst:
                                                rct = rst[0]
                                                if rct.emoji == '⭕':
                                                    # 판매 시도
                                                    try:
                                                        await mmgr.sell(item, count)
                                                    except mgrerrors.NotFound:
                                                        await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_sell_not_found', delafter=7), delete_after=7)
                                                        self.msglog.log(ctx, '[상점: 아이템 판매: 아이템 찾을 수 없음]')
                                                    else:
                                                        await ctx.send(embed=await self.embedmgr.get(ctx,'Market_sell_done', item, count))
                                                        self.msglog.log(ctx, '[상점: 아이템 판매: 완료]')
                                                elif rct.emoji == '❌':
                                                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled', delafter=7), delete_after=7)
                                                    self.msglog.log(ctx, '[상점: 아이템 판매: 취소]')
                                            await finalmsg.delete()
                                        else:
                                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_sell_too_many', item, delafter=7), delete_after=7)
                                            self.msglog.log(ctx, '[상점: 아이템 판매: 아이템 부족]')
                                    else:
                                        await ctx.send(embed=await self.embedmgr.get(ctx, 'Item_count_overthan_one', delafter=7), delete_after=7)
                                        self.msglog.log(ctx, '[상점: 아이템 판매: 1 이상이여야 함]')
                            else:
                                await ctx.send(embed=await self.embedmgr.get(ctx, 'Invalid_item_index', delafter=7), delete_after=7)
                                self.msglog.log(ctx, '[상점: 아이템 판매: 올바르지 않은 번째수]')

                elif reaction.emoji == '💎':
                    # 상점아이템 구매 섹션
                    itemidxmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_buy_select_item'))
                    self.msglog.log(ctx, '[상점: 아이템 구매: 번째수 입력]')
                    await itemidxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))

                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                            itemidx = int(idxtaskrst.content) - 1
                            item: MarketItem = pgr.get_thispage()[itemidx]
                            itemcountmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_buy_count'))
                            self.msglog.log(ctx, '[상점: 아이템 구매: 개수 입력]')
                            await itemcountmsg.add_reaction('❌')
                            canceltask2 = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemcountmsg, emojis=['❌'], timeout=60))
                            counttask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))
                            task2 = await event_waiter.wait_for_first(canceltask2, counttask)
                            await itemcountmsg.delete()
                            if task2 == counttask:
                                counttaskrst = counttask.result()
                                count = int(counttaskrst.content)
                                if item.discount is None:
                                    final_price = count * item.price
                                else:
                                    final_price = count * item.discount

                                if count >= 1:
                                    if final_price <= char.money:
                                        # 최종적 구매 확인
                                        embed = await self.embedmgr.get(ctx, 'Market_item', item, mode='buy', chardata=char, count=count)
                                        finalmsg = await ctx.send(embed=embed)
                                        await finalmsg.add_reaction('⭕')
                                        await finalmsg.add_reaction('❌')
                                        rst = await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=finalmsg, emojis=['⭕', '❌'], timeout=60)
                                        if rst:
                                            rct = rst[0]
                                            if rct.emoji == '⭕':
                                                # 캐릭터 갱신 후 다시 한번 잔고 충분한지 확인
                                                try:
                                                    await mmgr.buy(item, count)
                                                except mgrerrors.NotEnoughMoney:
                                                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_buy_not_enough_money', char.uid, final_price, delafter=7), delete_after=7)
                                                    self.msglog.log(ctx, '[상점: 아이템 구매: 돈 부족]')
                                                else:
                                                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_buy_done', item, count))
                                                    self.msglog.log(ctx, '[상점: 아이템 구매: 완료]')
                                            elif rct.emoji == '❌':
                                                await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled', delafter=7), delete_after=7)
                                                self.msglog.log(ctx, '[상점: 아이템 구매: 취소]')
                                        await finalmsg.delete()
                                    else:
                                        #돈 부족
                                        await ctx.send(embed=await self.embedmgr.get(ctx, 'NotEnoughMoney', more_required=final_price-char.money, delafter=7), delete_after=7)
                                        self.msglog.log(ctx, '[상점: 아이템 구매: 돈 부족]')
                                else:
                                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Item_count_overthan_one', delafter=7), delete_after=7)
                                    self.msglog.log(ctx, '[상점: 아이템 구매: 1 이상이여야 함]')
                        else:
                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Invalid_item_index', delafter=7), delete_after=7)
                            self.msglog.log(ctx, '[상점: 아이템 구매: 올바르지 않은 번째수]')

                elif reaction.emoji == '❔':
                    # 상점아이템 정보 확인 섹션
                    itemidxmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_info_select_item'))
                    self.msglog.log(ctx, '[상점: 아이템 정보: 번째수 입력]')
                    await itemidxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))
                    
                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await itemidxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                            itemidx = int(idxtaskrst.content) - 1
                            infoitem = pgr.get_thispage()[itemidx]
                            embed = await self.embedmgr.get(ctx, 'Market_item', infoitem, xtoclose=True)
                            iteminfomsg = await ctx.send(embed=embed)
                            self.msglog.log(ctx, '[상점: 아이템 정보]')
                            await iteminfomsg.add_reaction('❌')
                            await event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=iteminfomsg, emojis=['❌'], timeout=60*5)
                            await iteminfomsg.delete()
                        else:
                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Market_info_invalid_index', delafter=7), delete_after=7)
                            self.msglog.log(ctx, '[상점: 아이템 정보: 올바르지 않은 번째수]')

                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                if asyncio.iscoroutine(do):
                    await asyncio.gather(do,
                        msg.edit(embed=await self.embedmgr.get(ctx, 'Market', pgr)),
                    )

    @commands.command(name='내정보', aliases=['능력치', '스탯', '나'])
    async def _stat(self, ctx: commands.Context, charname: typing.Optional[str] = None):
        cmgr = CharMgr(self.pool)
        if not charname:
            char = await cmgr.get_current_char(ctx.author.id)
        else:
            char = await cmgr.get_character_by_name(charname)
            if not char:
                embed = await self.embedmgr.get(ctx, 'CharNotFound', charname)
                await ctx.send(embed=embed)
                return
        
        await ctx.send(embed=await self.embedmgr.get(ctx, 'Stat', char))
        self.msglog.log(ctx, '[내정보]')

    @commands.command(name='출석체크', aliases=['돈받기', '돈줘', '돈내놔', '출첵', '출석'])
    async def _getmoney(self, ctx: commands.Context):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                cmgr = CharMgr(self.pool)
                char = await cmgr.get_current_char(ctx.author.id)
                samgr = StatMgr(self.pool, char.uid, self.getlistener('on_levelup'))
                edgr = ExpTableDBMgr(self.datadb)
                rawchar = await cmgr.get_raw_character(char.uid)
                rcv_money = rawchar['received_money']
                now = datetime.datetime.now()
                level = await samgr.get_level(edgr)
                xp = round(edgr.get_required_exp(level)/100*2+50)
                embed = await self.embedmgr.get(ctx, 'Getmoney_done', 5000, xp)
                if rcv_money is None:
                    pass
                elif now.year == rcv_money.year and now.month == rcv_money.month and now.day <= rcv_money.day:
                    await ctx.send(ctx.author.mention, embed=await self.embedmgr.get(ctx, 'Getmoney_already'))
                    self.msglog.log(ctx, '[돈받기: 이미 받음]')
                    return
                imgr = ItemMgr(self.pool, char.uid)
                await imgr.give_money(5000)
                await samgr.give_exp(xp, edgr, ctx)
                await cur.execute('update chardata set received_money=%s where uuid=%s', (now, char.uid))
                await ctx.send(ctx.author.mention, embed=embed)
                self.msglog.log(ctx, '[돈받기: 완료]')

    @commands.command(name='지도', aliases=['내위치', '위치', '현재위치', '맵'])
    async def _map(self, ctx: commands.Context):
        cmgr = CharMgr(self.pool)
        char = await cmgr.get_current_char(ctx.author.id)
        
        await ctx.send(embed=await self.embedmgr.get(ctx, 'Map', char))
        self.msglog.log(ctx, '[지도]')

    @commands.command(name='이동', aliases=['워프'])
    async def _warp(self, ctx: commands.Context):
        cmgr = CharMgr(self.pool)
        char = await cmgr.get_current_char(ctx.author.id)
        rdgr = RegionDBMgr(self.datadb)
        rgn = rdgr.get_warpables("azalea")
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Warp_select_region', char))
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
            await cmgr.move_to(char.uid, region)
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Warp_done', region))
            self.msglog.log(ctx, '[이동: 완료]')

    @commands.guild_only()
    @commands.group(name='순위', aliases=['랭킹'], invoke_without_command=True)
    async def _rank(self, ctx: commands.Context):
        cmd = discord.utils.get(self.client.get_command('순위').commands, name='서버')
        await cmd(ctx)
    
    @_rank.command(name='서버', aliases=['길드', '섭'])
    async def _rank_server(self, ctx: commands.Context):
        cmgr = CharMgr(self.pool)
        rank = await cmgr.get_ranking(ctx.guild)
        pgr = pager.Pager(rank, 5)
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Rank', pgr, guild=ctx.guild))
        self.msglog.log(ctx, '[순위: 서버]')
        if len(pgr.pages()) <= 1:
            return
        for emj in emojibuttons.PageButton.emojis:
            await msg.add_reaction(emj)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emojibuttons.PageButton.emojis
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except:
                    pass
            else:
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr, double=7)
                if asyncio.iscoroutine(do):
                    await asyncio.gather(do,
                        msg.edit(embed=await self.embedmgr.get(ctx, 'Rank', pgr, guild=ctx.guild)),
                    )

    @_rank.command(name='전체', aliases=['올', '전부', '모두', '글로벌'])
    async def _rank_global(self, ctx: commands.Context):
        cmgr = CharMgr(self.pool)
        rank = await cmgr.get_ranking()
        pgr = pager.Pager(rank, 5)
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Rank', pgr, where='global'))
        self.msglog.log(ctx, '[순위: 전체]')
        if len(pgr.pages()) <= 1:
            return
        for emj in emojibuttons.PageButton.emojis:
            await msg.add_reaction(emj)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emojibuttons.PageButton.emojis
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except:
                    pass
            else:
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr, double=7)
                if asyncio.iscoroutine(do):
                    await asyncio.gather(do,
                        msg.edit(embed=await self.embedmgr.get(ctx, 'Rank', pgr, where='global')),
                    )

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)