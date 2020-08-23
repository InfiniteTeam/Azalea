import discord
from discord.ext import commands
import asyncio
import datetime
from utils.basecog import BaseCog
from utils import errors

class BaseCmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(client.get_data('check').master)

    @commands.group(name='ext', aliases=['확장'])
    async def _ext(self, ctx: commands.Context):
        pass

    @_ext.command(name='list', aliases=['목록'])
    async def _ext_list(self, ctx: commands.Context):
        await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_list'))
        self.msglog.log(ctx, '[전체 확장 목록]')

    @_ext.command(name='reload', aliases=['리로드'])
    async def _ext_reload(self, ctx: commands.Context, *names):
        reloads = self.client.extensions
        if (not names) or ('*' in names):
            for onename in reloads:
                self.client.reload_extension(onename)
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_reload', reloads))
            self.msglog.log(ctx, '[모든 확장 리로드 완료]')
        else:
            try:
                for onename in names:
                    if not (onename in reloads):
                        raise commands.ExtensionNotLoaded(f'로드되지 않은 확장: {onename}')
                for onename in names:
                    self.client.reload_extension(onename)
            except commands.ExtensionNotLoaded:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_unloaded', onename))
                self.msglog.log(ctx, '[로드되지 않았거나 존재하지 않는 확장]')
            else:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_reload_done', names))
                self.msglog.log(ctx, '[확장 리로드 완료]')
        
    @_ext.command(name='load', aliases=['로드'])
    async def _ext_load(self, ctx: commands.Context, *names):
        if not names or '*' in names:
            loads = list(set(self.client.get_data('allexts')) - set(self.client.extensions.keys()))
            try:
                if len(loads) == 0:
                    raise commands.ExtensionAlreadyLoaded('모든 확장이 이미 로드되었습니다.')
                for onename in loads:
                    self.client.load_extension(onename)
                    
            except commands.ExtensionAlreadyLoaded:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_all_loaded_already'))
                self.msglog.log(ctx, '[모든 확장이 이미 로드됨]')
            else:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_load_done', loads))
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
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_not_found', onename))
                self.msglog.log(ctx, '[존재하지 않는 확장]')
            except commands.ExtensionAlreadyLoaded:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_already_loaded', onename))
                self.msglog.log(ctx, '[이미 로드된 확장]')
            else:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_load_done', names))
                self.msglog.log(ctx, '[확장 로드 완료]')

    @_ext.command(name='unload', aliases=['언로드'])
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
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_not_loaded_any'))
                self.msglog.log(ctx, '[로드된 확장이 전혀 없음]')
            else:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Ext_unloaded_all', unloads))
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
                embed = discord.Embed(description=f'**❌ 로드되지 않은 확장입니다: `{onename}`**', color=self.color['error'])
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[로드되지 않은 확장]')
            except errors.LockedExtensionUnloading:
                embed = discord.Embed(description=f'**🔐 잠긴 확장은 언로드할 수 없습니다: `{lockedinnames}`**', color=self.color['error'])
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[잠긴 확장 로드 시도]')
            else:
                embed = discord.Embed(description=f'**{self.emj.get(ctx, "check")} 확장 언로드를 완료했습니다: `{", ".join(names)}`**', color=self.color['info'])
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[확장 언로드 완료]')

    @commands.command(name='reload', aliases=['리', '리로드'])
    async def _ext_reload_wrapper(self, ctx: commands.Context, *names):
        await self._ext_reload(ctx, *names)
        self.datadb.reload()
        await ctx.send(embed=discord.Embed(description='**내부 데이터베이스를 모두 리로드했습니다.**', color=self.color['info']))
        self.embedmgr.reload()
        await ctx.send(embed=discord.Embed(description='**임베드 매니저를 리로드했습니다.**', color=self.color['info']))

def setup(client):
    cog = BaseCmds(client)
    client.add_cog(cog)