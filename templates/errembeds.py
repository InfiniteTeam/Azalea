import discord
from discord.ext import commands

class MissingArgs:
    @classmethod
    def getembed(cls, prefix, color, paramdesc):
        return discord.Embed(title='❗ 명령어에 빠진 부분이 있습니다!', description=f'**`{paramdesc}`이(가) 필요합니다!**\n자세한 명령어 사용법은 `{prefix}도움` 을 통해 확인하세요!', color=color)

class CharNotFound:
    @classmethod
    def getembed(cls, ctx: commands.Context, charname):
        return discord.Embed(title=f'❓ 존재하지 않는 캐릭터입니다!: `{charname}`', color=ctx.bot.get_data('color')['error'])