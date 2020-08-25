import discord
from discord.ext import commands
import asyncio
from utils.basecog import BaseCog
from utils.datamgr import CharMgr, ItemMgr, ItemData, ItemDBMgr, FarmMgr, FarmDBMgr, FarmPlantStatus, StatMgr
from utils.pager import Pager
from utils import event_waiter, mgrerrors
import typing

class Farmcmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            cmd.add_check(self.check.char_online)

    @commands.group(name='농장', aliases=['밭', '텃밭', '농업', '농사'], invoke_without_command=True)
    async def _farm(self, ctx: commands.Context, *, charname: typing.Optional[str]):
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname)
            if not char:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', charname))
                self.msglog.log(ctx, '[농장: 존재하지 않는 캐릭터]')
                return
        else:
            char = await cmgr.get_current_char(ctx.author.id)
            charname = char.name

        embed = await self.embedmgr.get(ctx, 'Farm_dashboard', char)
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[농장]')

    @commands.command(name='심기')
    async def _simgi(self, ctx: commands.Context):
        cmgr = CharMgr(self.pool)
        char = await cmgr.get_current_char(ctx.author.id)
        idgr = ItemDBMgr(self.datadb)
        imgr = ItemMgr(self.pool, char.uid)
        farm_mgr = FarmMgr(self.pool, char.uid)
        farm_dmgr = FarmDBMgr(self.datadb)
        plantable = list(filter(lambda x: idgr.fetch_item(x.id).meta.get('plantable'), await imgr.get_items()))
        pgr = Pager(plantable, perpage=8)
        if await farm_mgr.get_free_space() == 0:
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_lack_of_space', 7), delete_after=7)
            self.msglog.log(ctx, '[심기: 농장 공간 부족]')
        elif len(pgr.pages()) == 0:
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_no_any_seed'))
        else:
            msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_backpack', pgr, char.uid, mode='select'))
            itemidxmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_select'))
            self.msglog.log(ctx, '[심기: 번째수 입력]')
            await itemidxmsg.add_reaction('❌')
            canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=itemidxmsg, emojis=['❌'], timeout=60))
            indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))
            task = await event_waiter.wait_for_first(canceltask, indextask)
            await itemidxmsg.delete()

            if task == indextask:
                idxtaskrst = indextask.result()
                if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                    itemidx = int(idxtaskrst.content) - 1
                    item: ItemData = pgr.get_thispage()[itemidx]
                    itemcountmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_count', min([await farm_mgr.get_free_space(), item.count])))
                    self.msglog.log(ctx, '[심기: 개수 입력]')
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
                                free = await farm_mgr.get_free_space()
                                if count <= free:
                                    plantid = idgr.fetch_item(item.id).meta.get('farm_plant')
                                    await imgr.delete_item(item, count)
                                    await farm_mgr.add_plant(self.datadb, plantid, count)
                                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_done', farm_dmgr.fetch_plant(plantid).title, count))
                                    self.msglog.log(ctx, '[심기: 완료]')
                                else:
                                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_lack_of_space_count', delafter=7), delete_after=7)
                                    self.msglog.log(ctx, '[심기: 농장 공간 부족]')
                            else:
                                await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_lack_of_item', item.count, delafter=7), delete_after=7)
                                self.msglog.log(ctx, '[심기: 아이템 부족]')
                        else:
                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_item_overthan_one', delafter=7), delete_after=7)
                            self.msglog.log(ctx, '[심기: 1 이상이여야 함]')
                else:
                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Plantplant_invalid_item_index', delafter=7), delete_after=7)
                    self.msglog.log(ctx, '[심기: 올바르지 않은 번째수]')
            await msg.delete()

    @commands.command(name='수확')
    async def _suhwak(self, ctx: commands.Context):
        cmgr = CharMgr(self.pool)
        char = await cmgr.get_current_char(ctx.author.id)
        smgr = StatMgr(self.pool, char.uid, self.getlistener('on_levelup'))
        farm_mgr = FarmMgr(self.pool, char.uid)
        can_harvest = await farm_mgr.get_plants_with_status(FarmPlantStatus.AllGrownUp)
        if not can_harvest:
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Harvest_no_any'))
            return

        plants = { one.id: None for one in can_harvest }
        for pid in plants.keys():
            plants[pid] = list(filter(lambda x: x.id == pid, can_harvest))

        
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Harvest', plants, can_harvest))
        self.msglog.log(ctx, '[수확]')
        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
        else:
            if reaction.emoji == '⭕':
                try:
                    await farm_mgr.harvest(smgr, self.datadb, *can_harvest, channel_id=ctx.channel.id)
                except mgrerrors.NotFound:
                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Harvest_plant_notfound'))
                else:
                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Harvest_done', can_harvest))

            elif reaction.emoji == '❌':
                try:
                    await msg.delete()
                except:
                    pass

def setup(client):
    cog = Farmcmds(client)
    client.add_cog(cog)
