import discord

class MissingArgs:
    @classmethod
    def getembed(cls, prefix, color, paramdesc):
        return discord.Embed(title='❗ 명령어에 빠진 부분이 있습니다!', description=f'**`{paramdesc}`이(가) 필요합니다!**\n자세한 명령어 사용법은 `{prefix}도움` 을 통해 확인하세요!', color=color)