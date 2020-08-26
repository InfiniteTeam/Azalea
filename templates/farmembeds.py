import discord
import math
from utils.basecog import BaseCog
from utils.datamgr import CharacterData, FarmMgr, FarmPlantStatus, FarmDBMgr, ItemDBMgr
from utils.embedmgr import aEmbedBase, aMsgBase


class Plantplant_lack_of_space(aEmbedBase):
    async def ko(self):
        embed = discord.Embed(
            title="❌ 농장 공간이 부족합니다!",
            description="농장에 빈 공간이 전혀 없습니다! 수확을 기다리거나 작물 재배를 취소해 공간을 늘릴 수 있습니다.",
            color=self.cog.color["error"],
        )

        return embed


class Plantplant_no_any_seed(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="📦 심을 수 있는 아이템이 하나도 없습니다!", color=self.cog.color["error"]
        )


class Plantplant_backpack(aEmbedBase):
    async def ko(self, *args, **kwargs):
        embed = await self.cog.embedmgr.get(self.ctx, "Backpack", *args, **kwargs)
        embed.set_author(name="🌱 심을 씨앗 선택하기")
        embed.set_footer(text="※ 심을 수 있는 아이템만 표시됩니다.")
        return embed


class Plantplant_select(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="🌱 작물 심기 - 아이템 선택",
            description="아이템의 번째수를 입력해주세요.\n위 메시지에 아이템 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.",
            color=self.cog.color["ask"],
        )


class Plantplant_count(aEmbedBase):
    async def ko(self, maxcount):
        return discord.Embed(
            title="🌱 작물 심기 - 심을 씨앗 개수",
            description="몇 개를 심으시겠어요? (최대 {}개)\n❌를 클릭해 취소합니다.".format(maxcount),
            color=self.cog.color["ask"],
        )


class Plantplant_done(aEmbedBase):
    async def ko(self, name, count):
        return discord.Embed(
            title="🌱 `{}` 을(를) {} 개 심었습니다!".format(name, count),
            color=self.cog.color["success"],
        )


class Plantplant_lack_of_space_count(aEmbedBase):
    async def ko(self, maxcount):
        embed = discord.Embed(
            title="❌ 농장 공간이 부족합니다!",
            description="현재 농장에 최대 {}개를 심을 수 있습니다.".format(maxcount),
            color=self.cog.color["error"],
        )

        return embed


class Plantplant_lack_of_item(aEmbedBase):
    async def ko(self, maxcount):
        embed = discord.Embed(
            title="❌ 아이템이 부족합니다!",
            description="이 아이템은 최대 {}개를 심을 수 있습니다.".format(maxcount),
            color=self.cog.color["error"],
        )

        return embed


class Plantplant_item_overthan_one(aEmbedBase):
    async def ko(self):
        embed = discord.Embed(
            title="❓ 아이템 개수는 적어도 1개 이상이여야 합니다!", color=self.cog.color["error"]
        )

        return embed


class Plantplant_invalid_item_index(aEmbedBase):
    async def ko(self):
        embed = discord.Embed(
            title="❓ 아이템 번째수가 올바르지 않습니다!",
            description="위 메시지에 아이템 앞마다 번호가 붙어 있습니다.",
            color=self.cog.color["error"],
        )

        return embed


class Farm_dashboard(aEmbedBase):
    async def ko(self, char: CharacterData):
        farm_mgr = FarmMgr(self.cog.pool, char.uid)
        level = await farm_mgr.get_level()
        area = await farm_mgr.get_area()
        embed = discord.Embed(
            title=f"🌲 `{char.name}` 의 농장", color=self.cog.color["info"]
        )
        embed.add_field(
            name="🔸 기본 정보", value="**레벨** `{}`\n**농장 크기**: `{}` 칸".format(level, area)
        )

        ls = [
            len(await farm_mgr.get_plants_with_status(FarmPlantStatus.AllGrownUp)),
            len(await farm_mgr.get_plants_with_status(FarmPlantStatus.Growing)),
        ]
        ls.append(area - sum(ls))

        statls = ["다 자람", "자라는 중", "빈 땅"]

        embed.add_field(
            name="🔸 작물 성장 상태",
            value="\n".join(
                [
                    "**{}** - {}칸 `({}%)`".format(
                        y, ls[idx], round(ls[idx] / area * 100)
                    )
                    for idx, y in enumerate(statls)
                ]
            ),
        )

        return embed


class Harvest_no_any(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="❌ 수확할 수 있는 작물이 하나도 없습니다!", color=self.cog.color["error"]
        )


class Harvest(aEmbedBase):
    async def ko(self, plants, can_harvest):
        farm_dmgr = FarmDBMgr(self.cog.datadb)
        embed = discord.Embed(
            title="🍎 수확하기",
            description="{}칸을 수확할 수 있습니다. 계속할까요?\n\n".format(len(can_harvest)),
            color=self.cog.color["info"],
        )
        for oid in plants.keys():
            plantdb = farm_dmgr.fetch_plant(oid)
            embed.description += "{} {}: `{}`칸\n".format(
                plantdb.icon, plantdb.title, len(plants[oid])
            )

        return embed


class Harvest_plant_notfound(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="❓ 수확할 수 있는 작물을 찾을 수 없습니다",
            description="이미 수확됐지는 않은가요?",
            color=self.cog.color["error"],
        )


class Harvest_done(aEmbedBase):
    async def ko(self, can_harvest):
        idgr = ItemDBMgr(self.cog.datadb)
        farm_dmgr = FarmDBMgr(self.cog.datadb)
        gotten_plants = {one.id: 0 for one in can_harvest}
        for one in can_harvest:
            gotten_plants[one.id] += one.count

        embed = discord.Embed(
            title="{} 성공적으로 수확했습니다!".format(self.cog.emj.get(self.ctx, "check")),
            description="수확으로 얻은 아이템:\n\n",
            color=self.cog.color["success"],
        )

        for k, v in gotten_plants.items():
            itemdb = idgr.fetch_item(farm_dmgr.fetch_plant(k).grown)
            embed.description += "{} {}: {}개\n".format(itemdb.icon, itemdb.name, v)

        return embed
