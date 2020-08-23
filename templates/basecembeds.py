import discord
from utils.embedmgr import aEmbedBase, aMsgBase

class Ext_list(aEmbedBase):
    async def _public_allexts(self):
        allexts = ''
        for oneext in self.cog.client.get_data('allexts'):
            if oneext == self.ctx.cog.__module__:
                allexts += f'🔐 {oneext}\n'
            elif oneext in self.cog.client.extensions:
                allexts += f'{self.cog.emj.get(self.ctx, "check")} {oneext}\n'
            else:
                allexts += f'{self.cog.emj.get(self.ctx, "cross")} {oneext}\n'
        return allexts

    async def ko(self):
        return discord.Embed(
            title=f'🔌 전체 확장 목록',
            color=self.cog.color['primary'],
            description="""\
                총 {}개 중 {}개 로드됨.
                {}
            """.format(
                len(self.cog.client.get_data('allexts')),
                len(self.cog.client.extensions),
                await self._public_allexts()
            )
        )

class Ext_reload(aEmbedBase):
    async def ko(self, reloads):
        embed = discord.Embed(
            description=f'**{self.cog.emj.get(self.ctx, "check")} 활성된 모든 확장을 리로드했습니다**',
            color=self.cog.color['info']
        )
        embed.set_footer(text=", ".join(reloads))
        return embed

class Ext_unloaded(aEmbedBase):
    async def ko(self, name):
        return discord.Embed(
            description=f'**❓ 로드되지 않았거나 존재하지 않는 확장입니다: `{name}`**',
            color=self.cog.color['error']
        )

class Ext_reload_done(aEmbedBase):
    async def ko(self, names):
        return discord.Embed(
            description=f'**{self.cog.emj.get(self.ctx, "check")} 확장 리로드를 완료했습니다: `{", ".join(names)}`**',
            color=self.cog.color['info']
        )

class Ext_all_loaded_already(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            description='**❌ 모든 확장이 이미 로드되었습니다!**',
            color=self.cog.color['error']
        )

class Ext_load_done(aEmbedBase):
    async def ko(self, loads):
        return discord.Embed(
            description=f'**{self.cog.emj.get(self.ctx, "check")} 확장 로드를 완료했습니다: `{", ".join(loads)}`**',
            color=self.cog.color['info']
        )

class Ext_not_found(aEmbedBase):
    async def ko(self, name):
        return discord.Embed(
            description=f'**❓ 존재하지 않는 확장입니다: `{name}`**',
            color=self.cog.color['error']
        )

class Ext_already_loaded(aEmbedBase):
    async def ko(self, name):
        return discord.Embed(
            description=f'**❌ 이미 로드된 확장입니다: `{name}`**',
            color=self.cog.color['error']
        )

class Ext_not_loaded_any(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            description='**❌ 로드된 확장이 하나도 없습니다!`**', 
            color=self.cog.color['error']
        )

class Ext_unloaded_all(aEmbedBase):
    async def ko(self, unloads):
        return discord.Embed(
            description=f'**{self.cog.emj.get(self.ctx, "check")} 확장 언로드를 완료했습니다: `{", ".join(unloads)}`**',
            color=self.cog.color['info']
        )