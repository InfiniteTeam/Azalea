import discord
from utils.embedmgr import aEmbedBase, aMsgBase


class Fishing_throw(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="🎣 낚시",
            description="찌를 던졌습니다! 뭔가가 걸리면 재빨리 ⁉ 반응을 클릭하세요!",
            color=self.cog.color["g-fishing"],
        )


class Fishing_caught_nothing(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="🎣 낚시",
            description='아무것도 잡히지 않았어요! 너무 빨리 당긴것 같아요.',
            color=self.cog.color["g-fishing"],
        )


class Fishing_something_caught(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="🎣 낚시",
            description='뭔가가 걸렸습니다! 지금이에요!',
            color=self.cog.color["g-fishing"],
        )

class Fishing_missed(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="🎣 낚시",
            description='놓쳐 버렸네요... 너무 천천히 당긴것 같아요.',
            color=self.cog.color["g-fishing"],
        )

class Fishing_done(aEmbedBase):
    async def ko(self, fish, exp):
        return discord.Embed(
            title="🎣 낚시 - 잡았습니다!",
            description='**`{}` 을(를)** 잡았습니다!\n+`{}` 경험치를 받았습니다.'.format(fish.name, exp),
            color=self.cog.color["g-fishing"],
        )