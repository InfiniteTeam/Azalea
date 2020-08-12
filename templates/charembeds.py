import discord
from utils.basecog import BaseCog
from utils.mgrerrors import CharCreateError, CharCreateErrReasons

def charcreate_fail_embed(cog: BaseCog, exc: CharCreateError):
    if exc.reason == CharCreateErrReasons.InvalidName:
        embed = discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='캐릭터 이름은 반드시 한글, 영어, 숫자만을 사용해야 합니다.\n다시 시도해 주세요!', color=cog.color['error'])
        return embed
    elif exc.reason == CharCreateErrReasons.InvalidLength:
        embed = discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='캐릭터 이름은 2~10글자이여야 합니다.\n다시 시도해 주세요!', color=cog.color['error'])
        return embed
    elif exc.reason == CharCreateErrReasons.NameAlreadyExists:
        embed = discord.Embed(title='❌ 이미 사용중인 이름입니다!', description='다시 시도해 주세요!', color=cog.color['error'])
        return embed
    else:
        for pfx in cog.client.command_prefix:
            if pfx.rstrip().lower() in m.content.lower():
                embed = discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='아젤리아 봇 접두사는 이름에 포함할 수 없습니다.\n다시 시도해 주세요!', color=cog.color['error'])
                return embed
    