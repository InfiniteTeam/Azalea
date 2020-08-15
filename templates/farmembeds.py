import discord
import math
from utils.basecog import BaseCog
from utils.datamgr import CharacterData, FarmMgr, FarmPlantStatus

async def farm_dashboard(cog: BaseCog, *, char: CharacterData, farm_mgr: FarmMgr):
    level = await farm_mgr.get_level()
    area = await farm_mgr.get_area()
    embed = discord.Embed(title=f'🌲 `{char.name}` 의 농장', color=cog.color['info'])
    embed.add_field(name='🔸 기본 정보', value='**레벨** `{}`\n**농장 크기**: `{}` 칸'.format(level, area))

    ls = [
        len(await farm_mgr.get_plants_with_status(FarmPlantStatus.AllGrownUp)),
        len(await farm_mgr.get_plants_with_status(FarmPlantStatus.Growing))
    ]
    ls.append(area - sum(ls))

    statls = [
        '다 자람',
        '자라는 중',
        '빈 땅'
    ]

    embed.add_field(
        name='🔸 작물 성장 상태',
        value='\n'.join(['**{}** - {}칸 `({}%)`'.format(y, ls[idx], round(ls[idx]/area*100)) for idx, y in enumerate(statls)])
    )

    return embed

async def farm_status(cog: BaseCog, *, char: CharacterData, farm_mgr: FarmMgr):
    area = await farm_mgr.get_area()

    ls = [
        len(await farm_mgr.get_plants_with_status(FarmPlantStatus.AllGrownUp)),
        len(await farm_mgr.get_plants_with_status(FarmPlantStatus.Growing))
    ]
    ls.append(area - sum(ls))

    statls = [
        '다 자람',
        '자라는 중',
        '빈 땅'
    ]

    embed = discord.Embed(title=f'🌱 `{char.name}` 의 농장 상태', description='', color=cog.color['info'])
    embed.add_field(
        name='🔸 작물 성장 상태',
        value='\n'.join(['**{}** - {}칸 `({}%)`'.format(y, ls[idx], round(ls[idx]/area*100)) for idx, y in enumerate(statls)])
    )

    return embed