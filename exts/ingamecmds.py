import discord
from discord.ext import commands
import datetime
import asyncio
import datetime
import json
from exts.utils import pager, itemmgr, emojibuttons, errors, charmgr
from exts.utils.basecog import BaseCog

class InGamecmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            if cmd.name != '캐릭터':
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
            chartype = one['type']
            online = one['online']
            onlinestr = ''
            if online:
                onlinestr = '(**현재 플레이중**)'
            charstr += '**{}** {}\n레벨: {} \\| 직업: {}'.format(name, onlinestr, level, chartype)
        embed = discord.Embed(
            title=f'🎲 `{ctx.author.name}`님의 캐릭터 목록',
            description=charstr,
            color=self.color['info'],
            timestamp=datetime.datetime.utcnow()
        )
        embed.description = charstr + '```{}/{} 페이지, 전체 {}개```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
        return embed

    @commands.group(name='캐릭터', aliases=['캐'], invoke_without_command=True)
    async def _char(self, ctx: commands.Context):
        perpage = 4
        cmgr = charmgr.CharMgr(self.cur)
        chars = cmgr.get_characters(ctx.author.id)
        if not chars:
            await ctx.send(embed=discord.Embed(
                title='🎲 캐릭터가 하나도 없네요!',
                description='`{}생성` 명령으로 캐릭터를 생성해서 게임을 시작하세요!'.format(self.prefix),
                color=self.color['warn'],
                timestamp=datetime.datetime.utcnow()
            ))
            return
        pgr = pager.Pager(chars)
        msg = await ctx.send(embed=await self.char_embed(ctx, pgr))
        self.msglog.log(ctx, '[캐릭터 목록]')
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

        return

    @_char.command(name='생성')
    async def _char_creacte(self, ctx:commands.Context):
        self._char_creacte.name = '생성'
        await ctx.send('d')
            

def setup(client):
    cog = InGamecmds(client)
    client.add_cog(cog)