import discord
from discord.ext import commands
import asyncio
import random
from utils.basecog import BaseCog
from utils.datamgr import CharMgr, ItemDBMgr, ItemMgr, ItemData, StatMgr, ExpTableDBMgr
from db import exps
from db.itemtags import Tag

class Gamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            cmd.add_check(self.check.char_online)

    @commands.command(name='낚시')
    async def _fishing(self, ctx: commands.Context):
        cmgr = CharMgr(self.pool)
        char = await cmgr.get_current_char(ctx.author.id)
        idgr = ItemDBMgr(self.datadb)
        imgr = ItemMgr(self.pool, char.uid)
        edgr = ExpTableDBMgr(self.datadb)
        samgr = StatMgr(self.pool, char.uid, self.getlistener('on_levelup'))

        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Fishing_throw'))
        self.msglog.log(ctx, '[낚시: 시작]')
        emjs = ['⁉']
        await msg.add_reaction('⁉')
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs

        async def do():
            todo = []
            if ctx.channel.type == discord.ChannelType.text and msg.id == ctx.channel.last_message_id:
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
                embed = await self.embedmgr.get(ctx, 'Fishing_caught_nothing')
                self.msglog.log(ctx, '[낚시: 아무것도 잡히지 않음]')
                await do()
                return

        embed = await self.embedmgr.get(ctx, 'Fishing_something_caught')
        await msg.edit(embed=embed)

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=random.uniform(0.8, 1.7))
        except asyncio.TimeoutError:
            embed = await self.embedmgr.get(ctx, 'Fishing_missed')
            self.msglog.log(ctx, '[낚시: 놓침]')
            await do()
        else:
            if reaction.emoji == '⁉':
                fishes = idgr.fetch_items_with(tags=[Tag.Fish], meta={'catchable': True})
                fish = random.choices(fishes, list(map(lambda x: x.meta['percentage'], fishes)))[0]
                await imgr.give_item(ItemData(fish.id, 1, []))
                exp = exps.fishing(req=edgr.get_required_exp(await samgr.get_level(edgr)), fish=fish)
                await samgr.give_exp(exp, edgr, ctx)
                embed = await self.embedmgr.get(ctx, 'Fishing_done', fish, exp)
                self.msglog.log(ctx, '[낚시: 잡음]')
                await do()

def setup(client):
    cog = Gamecmds(client)
    client.add_cog(cog)
