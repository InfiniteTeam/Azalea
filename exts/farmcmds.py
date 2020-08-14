import discord
from discord.ext import commands
import asyncio
from utils.basecog import BaseCog
from utils.gamemgr import FarmMgr, FarmDBMgr, FarmPlantData, FarmPlantStatus
from utils.datamgr import CharMgr, ItemMgr, ItemData, ItemDBMgr
from utils.pager import Pager
from utils import event_waiter
from templates import miniembeds, farmembeds, ingameembeds
import typing
import datetime

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
                await ctx.send(embed=miniembeds.CharNotFound.getembed(ctx, charname))
                self.msglog.log(ctx, '[농장: 존재하지 않는 캐릭터]')
                return
        else:
            char = await cmgr.get_current_char(ctx.author.id)
            charname = char.name

        farm_mgr = FarmMgr(self.pool, char.uid)
        embed = await farmembeds.farm_dashboard(self, farm_mgr=farm_mgr, char=char)
        await ctx.send(embed=embed)

    @_farm.command(name='상태')
    async def _farm_status(self, ctx: commands.Context, *, charname: typing.Optional[str]):
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname)
            if not char:
                await ctx.send(embed=miniembeds.CharNotFound.getembed(ctx, charname))
                self.msglog.log(ctx, '[농장: 존재하지 않는 캐릭터]')
                return
        else:
            char = await cmgr.get_current_char(ctx.author.id)
            charname = char.name

        farm_mgr = FarmMgr(self.pool, char.uid)
        embed = await farmembeds.farm_status(self, char=char, farm_mgr=farm_mgr)
        await ctx.send(embed=embed)

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
            embed = discord.Embed(title='❌ 농장 공간이 부족합니다!', description='농장에 빈 공간이 전혀 없습니다! 수확을 기다리거나 작물 재배를 취소해 공간을 늘릴 수 있습니다.', color=self.color['error'])
            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
            await ctx.send(embed=embed, delete_after=7)
            self.msglog.log(ctx, '[심기: 농장 공간 부족]')
        elif len(pgr.pages()) == 0:
            await ctx.send(embed=discord.Embed(title='📦 심을 수 있는 아이템이 하나도 없습니다!', color=self.color['error']))
        else:
            embed = await ingameembeds.backpack_embed(self, ctx, pgr, char.uid, mode='select')
            embed.set_author(name='🌱 심을 씨앗 선택하기')
            embed.set_footer(text='※ 심을 수 있는 아이템만 표시됩니다.')
            msg = await ctx.send(embed=embed)
            itemidxmsg = await ctx.send(embed=discord.Embed(
                title='🌱 작물 심기 - 아이템 선택',
                description='아이템의 번째수를 입력해주세요.\n위 메시지에 아이템 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.',
                color=self.color['ask']
            ))
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
                    itemcountmsg = await ctx.send(embed=discord.Embed(
                        title='🌱 작물 심기 - 심을 씨앗 개수',
                        description='몇 개를 심으시겠어요? (최대 {}개)\n❌를 클릭해 취소합니다.'.format(min([await farm_mgr.get_free_space(), item.count])),
                        color=self.color['ask']
                    ))
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
                                    await farm_mgr.add_plant(farm_dmgr, plantid, count)
                                    await ctx.send(embed=discord.Embed(title='🌱 `{}` 을(를) {} 개 심었습니다!'.format(farm_dmgr.fetch_plant(plantid).title, count), color=self.color['success']))
                                else:
                                    embed = discord.Embed(title='❌ 농장 공간이 부족합니다!', description='현재 농장에 최대 {}개를 심을 수 있습니다.'.format(free), color=self.color['error'])
                                    embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                    await ctx.send(embed=embed, delete_after=7)
                                    self.msglog.log(ctx, '[심기: 농장 공간 부족]')
                            else:
                                embed = discord.Embed(title='❌ 아이템의 양이 너무 많습니다!', description='이 아이템은 최대 {}개를 심을 수 있습니다.'.format(item.count), color=self.color['error'])
                                embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                                await ctx.send(embed=embed, delete_after=7)
                                self.msglog.log(ctx, '[심기: 아이템 부족]')
                        else:
                            embed = discord.Embed(title='❓ 아이템 개수는 적어도 1개 이상이여야 합니다!', color=self.color['error'])
                            embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                            await ctx.send(embed=embed, delete_after=7)
                            self.msglog.log(ctx, '[심기: 1 이상이여야 함]')
                else:
                    embed = discord.Embed(title='❓ 아이템 번째수가 올바르지 않습니다!', description='위 메시지에 아이템 앞마다 번호가 붙어 있습니다.', color=self.color['error'])
                    embed.set_footer(text='이 메시지는 7초 후에 사라집니다')
                    await ctx.send(embed=embed, delete_after=7)
                    self.msglog.log(ctx, '[심기: 올바르지 않은 번째수]')
            await msg.delete()

    @commands.command(name='수확')
    async def _suhwak(self, ctx: commands.Context):
        cmgr = CharMgr(self.pool)
        char = await cmgr.get_current_char(ctx.author.id)
        farm_dmgr = FarmDBMgr(self.datadb)
        farm_mgr = FarmMgr(self.pool, char.uid)
        can_harvest = await farm_mgr.get_plants_with_status(FarmPlantStatus.AllGrownUp)
        plants = { one.id: None for one in can_harvest }
        for pid in plants.keys():
            plants[pid] = list(filter(lambda x: x.id == pid, can_harvest))

        embed = discord.Embed(title='🍎 수확하기', description='', color=self.color['info'])
        for oid in plants.keys():
            plantdb = farm_dmgr.fetch_plant(oid)
            allcount = sum(map(lambda x: x.count, plants[oid]))
            embed.description += '{}: `{}`개\n'.format(plantdb.title, allcount)
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[수확]')

def setup(client):
    cog = Farmcmds(client)
    client.add_cog(cog)
