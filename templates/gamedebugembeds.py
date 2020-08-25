import discord
from utils.embedmgr import aEmbedBase
from utils.datamgr import ExpTableDBMgr

class Give_not_exists(aEmbedBase):
    async def ko(self, itemid):
        return discord.Embed(
            title=f"❓ 존재하지 않는 아이템 아이디: {itemid}", color=self.cog.color["error"]
        )


class Give(aEmbedBase):
    async def ko(self, item, count, enchantments, char):
        embed = discord.Embed(
            title="📦 아이템 받기",
            description="다음과 같이 아이템을 받습니다. 계속할까요?",
            color=self.cog.color["ask"],
        )
        embed.add_field(
            name="아이템", value="[ {} ] {} {}".format(item.id, item.icon, item.name)
        )
        embed.add_field(name="개수", value=f"{count}개")
        enchantstrlist = [
            f"{enchant.name}: {enchant.level}" for enchant in enchantments
        ]
        enchantstr = "\n".join(enchantstrlist)
        if not enchantstr:
            enchantstr = "(없음)"
        embed.add_field(name="받는 캐릭터", value=char.name)
        embed.add_field(name="마법부여", value=enchantstr, inline=False)
        return embed


class Give_done(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="{} 아이템을 성공적으로 받았습니다!".format(self.cog.emj.get(self.ctx, "check")),
            color=self.cog.color["success"],
        )


class Giveexp_done(aEmbedBase):
    async def ko(self, exp):
        return discord.Embed(
            title="{} 경험치 {} 만큼 성공적으로 주었습니다!".format(self.cog.emj.get(self.ctx, "check"), exp),
            color=self.cog.color["success"],
        )


class Giveexp(aEmbedBase):
    async def ko(self, char, nowexp, exp, lv):
        edgr = ExpTableDBMgr(self.cog.datadb)
        embed = discord.Embed(title='🏷 경험치 지급하기', description='다음과 같이 계속할까요?', color=self.cog.color['warn'])
        embed.add_field(name='경험치 변동', value=f'{nowexp} → {nowexp+exp}')
        embed.add_field(name='레벨 변동', value='{} → {}'.format(lv, edgr.clac_level(nowexp+exp)))
        embed.add_field(name='대상 캐릭터', value=char.name)
        return embed