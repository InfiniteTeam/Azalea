import discord
from discord.ext import commands
import asyncio
import random
from exts.utils.basecog import BaseCog
from exts.utils.datamgr import CharMgr, ItemDBMgr, ItemMgr, ItemData

class Gamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            cmd.add_check(self.check.char_online)

    @commands.command(name='낚시')
    async def _fishing(self, ctx: commands.Context):
        cmgr = CharMgr(self.cur)
        embed = discord.Embed(title='🎣 낚시', description='찌를 던졌습니다! 뭔가가 걸리면 재빨리 ⁉ 반응을 클릭하세요!', color=self.color['g-fishing'])
        msg = await ctx.send(embed=embed)
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
                embed.description = '아무것도 잡히지 않았어요! 너무 빨리 당긴것 같아요.'
                self.msglog.log(ctx, '[낚시: 아무것도 잡히지 않음]')
                await do()
                return
        embed.description = '뭔가가 걸렸습니다! 지금이에요!'
        await msg.edit(embed=embed)

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=random.uniform(0.8, 1.7))
        except asyncio.TimeoutError:
            embed.description = '놓쳐 버렸네요... 너무 천천히 당긴것 같아요.'
            self.msglog.log(ctx, '[낚시: 놓침]')
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
                self.msglog.log(ctx, '[낚시: 잡음]')
                await do()