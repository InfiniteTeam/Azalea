import discord
from discord.ext import commands
import asyncio
import datetime
from exts.utils.basecog import BaseCog
from exts.utils import errors

class BaseCmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(client.get_data('check').master)

    @commands.group(name='ext')
    async def _ext(self, ctx: commands.Context):
        pass

    @_ext.command(name='list')
    async def _ext_list(self, ctx: commands.Context):
        allexts = ''
        for oneext in self.client.get_data('allexts'):
            if oneext == __name__:
                allexts += f'🔐 {oneext}\n'
            elif oneext in self.client.extensions:
                allexts += f'{self.emj.get(ctx, "check")} {oneext}\n'
            else:
                allexts += f'{self.emj.get(ctx, "cross")} {oneext}\n'
        embed = discord.Embed(title=f'🔌 전체 확장 목록', color=self.color['primary'], timestamp=datetime.datetime.utcnow(), description=
            f"""\
                총 {len(self.client.get_data('allexts'))}개 중 {len(self.client.extensions)}개 로드됨.
                {allexts}
            """
        )
        await ctx.send(embed=embed)
        self.msglog.log(ctx, '[전체 확장 목록]')

    @_ext.command(name='reload')
    async def _ext_reload(self, ctx: commands.Context, *names):
        reloads = self.client.extensions
        if (not names) or ('*' in names):
            for onename in reloads:
                self.client.reload_extension(onename)
            embed = discord.Embed(description=f'**{self.emj.get(ctx, "check")} 활성된 모든 확장을 리로드했습니다: `{", ".join(reloads)}`**', color=self.color['info'], timestamp=datetime.datetime.utcnow())
            await ctx.send(embed=embed)
            self.msglog.log(ctx, '[모든 확장 리로드 완료]')
        else:
            try:
                for onename in names:
                    if not (onename in reloads):
                        raise commands.ExtensionNotLoaded(f'로드되지 않은 확장: {onename}')
                for onename in names:
                    self.client.reload_extension(onename)
            except commands.ExtensionNotLoaded:
                embed = discord.Embed(description=f'**❓ 로드되지 않았거나 존재하지 않는 확장입니다: `{onename}`**', color=self.color['error'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[로드되지 않았거나 존재하지 않는 확장]')
            else:
                embed = discord.Embed(description=f'**{self.emj.get(ctx, "check")} 확장 리로드를 완료했습니다: `{", ".join(names)}`**', color=self.color['info'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[확장 리로드 완료]')
        
    @_ext.command(name='load')
    async def _ext_load(self, ctx: commands.Context, *names):
        if not names or '*' in names:
            loads = list(set(self.client.get_data('allexts')) - set(self.client.extensions.keys()))
            try:
                if len(loads) == 0:
                    raise commands.ExtensionAlreadyLoaded('모든 확장이 이미 로드되었습니다.')
                for onename in loads:
                    self.client.load_extension(onename)
                    
            except commands.ExtensionAlreadyLoaded:
                embed = discord.Embed(description='**❌ 모든 확장이 이미 로드되었습니다!**', color=self.color['error'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[모든 확장이 이미 로드됨]')
            else:
                embed = discord.Embed(description=f'**{self.emj.get(ctx, "check")} 확장 로드를 완료했습니다: `{", ".join(loads)}`**', color=self.color['info'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[확장 로드 완료]')
        else:
            try:
                for onename in names:
                    if not (onename in self.client.get_data('allexts')):
                        raise commands.ExtensionNotFound(f'존재하지 않는 확장: {onename}')
                    if onename in self.client.extensions:
                        raise commands.ExtensionAlreadyLoaded(f'이미 로드된 확장: {onename}')
                for onename in names:
                    self.client.load_extension(onename)

            except commands.ExtensionNotFound:
                embed = discord.Embed(description=f'**❓ 존재하지 않는 확장입니다: `{onename}`**', color=self.color['error'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[존재하지 않는 확장]')
            except commands.ExtensionAlreadyLoaded:
                embed = discord.Embed(description=f'**❌ 이미 로드된 확장입니다: `{onename}`**', color=self.color['error'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[이미 로드된 확장]')
            else:
                embed = discord.Embed(description=f'**{self.emj.get(ctx, "check")} 확장 로드를 완료했습니다: `{", ".join(names)}`**', color=self.color['info'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[확장 로드 완료]')

    @_ext.command(name='unload')
    async def _ext_unload(self, ctx: commands.Context, *names):
        if not names or '*' in names:
            unloads = list(self.client.extensions.keys())
            unloads = list(filter(lambda ext: ext not in self.client.get_data('lockedexts'), unloads))
            try:
                if len(unloads) == 0:
                    raise commands.ExtensionNotLoaded('로드된 확장이 하나도 없습니다!')
                for onename in unloads:
                    self.client.unload_extension(onename)
            except commands.ExtensionNotLoaded:
                embed = discord.Embed(description='**❌ 로드된 확장이 하나도 없습니다!`**', color=self.color['error'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[로드된 확장이 전혀 없음]')
            else:
                embed = discord.Embed(description=f'**{self.emj.get(ctx, "check")} 확장 언로드를 완료했습니다: `{", ".join(unloads)}`**', color=self.color['info'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[열린 모든 확장 언로드 완료]')
        else:
            try:
                if set(names) >= set(self.client.get_data('lockedexts')):
                    lockedinnames = ", ".join(set(names) & set(self.client.get_data("lockedexts")))
                    raise errors.LockedExtensionUnloading('잠긴 확장은 언로드할 수 없습니다: ' + lockedinnames)
                for onename in names:
                    if not (onename in self.client.extensions):
                        raise commands.ExtensionNotLoaded(f'로드되지 않은 확장: {onename}')
                for onename in names:
                    self.client.unload_extension(onename)

            except commands.ExtensionNotLoaded:
                embed = discord.Embed(description=f'**❌ 로드되지 않은 확장입니다: `{onename}`**', color=self.color['error'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[로드되지 않은 확장]')
            except errors.LockedExtensionUnloading:
                embed = discord.Embed(description=f'**🔐 잠긴 확장은 언로드할 수 없습니다: `{lockedinnames}`**', color=self.color['error'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[잠긴 확장 로드 시도]')
            else:
                embed = discord.Embed(description=f'**{self.emj.get(ctx, "check")} 확장 언로드를 완료했습니다: `{", ".join(names)}`**', color=self.color['info'], timestamp=datetime.datetime.utcnow())
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[확장 언로드 완료]')

    @commands.command(name='r')
    async def _ext_reload_wrapper(self, ctx: commands.Context, *names):
        await self._ext_reload(ctx, *names)

    @commands.command(name='long')
    async def _long(self, ctx: commands.Context, *names):
        await ctx.send('d'*20000)

def setup(client):
    cog = BaseCmds(client)
    client.add_cog(cog)