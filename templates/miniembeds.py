import discord
from discord.ext import commands
from utils.basecog import BaseCog
from utils.embedmgr import aEmbedBase

def set_delete_after_footer(embed: discord.Embed, delafter: int):
    if delafter:
        embed.set_footer(text=f'이 메시지는 {delafter}초 후에 사라집니다')
        return True
    return False

class Canceled(aEmbedBase):
    async def ko(self, delafter: int=None):
        embed = discord.Embed(title='❌ 취소되었습니다.', color=self.cog.color['error'])
        set_delete_after_footer(embed, delafter)
        return embed
    
    async def en(self, delafter: int=None):
        embed = discord.Embed(title='❌ Canceled.', color=self.cog.color['error'])
        set_delete_after_footer(embed, delafter)
        return embed

class MissingArgs(aEmbedBase):
    def ko(self, paramdesc):
        return discord.Embed(
            title='❗ 명령어에 빠진 부분이 있습니다!',
            description=f'**`{paramdesc}`이(가) 필요합니다!**\n자세한 명령어 사용법은 `{self.cog.prefix}도움` 을 통해 확인하세요!',
            color=self.cog.color['error']
        )

class CharNotFound:
    @classmethod
    def getembed(cls, ctx: commands.Context, charname):
        return discord.Embed(title=f'❓ 존재하지 않는 캐릭터입니다!: `{charname}`', color=ctx.bot.get_data('color')['error'])

class Public:
    @staticmethod
    def invalid(cog: BaseCog, *, target: str, description: str='', delafter: int=7):
        embed = discord.Embed(title=f'❓ {target} (이)가 올바르지 않습니다!', description=description, color=cog.color['error'])
        set_delete_after_footer(embed, delafter)
        return embed

class CountError:
    @staticmethod
    def must_be_over_than(cog: BaseCog, *, target: str, overthan: int, delafter: int=7):
        embed = discord.Embed(title=f'❓ {target}(은)는 적어도 {overthan} 이상이여야 합니다!', color=cog.color['error'])
        set_delete_after_footer(embed, delafter)
        return embed

class MoneyError:
    @staticmethod
    def not_enough_money(cog: BaseCog, *, more_required: int, delafter: int=7):
        embed = discord.Embed(title='❓ 돈이 부족합니다!', description=f'`{more_required}`골드가 부족합니다!', color=cog.color['error'])
        set_delete_after_footer(embed, delafter)
        return embed
