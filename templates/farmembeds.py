import discord
import math
from utils.basecog import BaseCog
from utils.gamemgr import FarmMgr, FarmPlantStatus
from utils.datamgr import CharacterData

async def farm_dashboard(cog: BaseCog, *, char: CharacterData, farm_mgr: FarmMgr):
    level = await farm_mgr.get_level()
    area = await farm_mgr.get_area()
    embed = discord.Embed(title=f'🌲 `{char.name}` 의 농장', color=cog.color['info'])
    embed.add_field(name='기본 정보', value='**레벨** `{}`\n**농장 크기**: `{}` 칸'.format(level, area))
    return embed

async def farm_status(cog: BaseCog, *, char: CharacterData, farm_mgr: FarmMgr):
    area = await farm_mgr.get_area()
    nulbi = 81
    
    ls = [
        round(len(await farm_mgr.get_plants_with_status(FarmPlantStatus.AllGrownUp)) / area * nulbi),
        round(len(await farm_mgr.get_plants_with_status(FarmPlantStatus.Growing)) / area * nulbi),
        round(len(await farm_mgr.get_plants_with_status(FarmPlantStatus.Sprouted)) / area * nulbi),
        round(len(await farm_mgr.get_plants_with_status(FarmPlantStatus.Planted)) / area * nulbi)
    ]
    ls.append(nulbi - sum(ls))

    stats = list('🟥' * ls[0] + '🟨' * ls[1] + '🟩' * ls[2] + '⬜' * ls[3] + '🟫' * ls[4])
    for x in range(9):
        stats.insert(10*x, '\n')

    statls = [
        '🟥 다 자람',
        '🟨 자라는 중',
        '🟩 싹이 틈',
        '⬜ 아직 싹이 트지 않음',
        '🟫 빈 땅'
    ]

    statstat = []
    for idx, y in enumerate(statls):
        statstat.append('{} - {}%'.format(y, round(ls[idx]/nulbi*100)))

    embed = discord.Embed(title=f'🌱 `{char.name}` 의 농장 상태', color=cog.color['info'])
    embed.add_field(name='농장 작물 차지 비율', value=''.join(stats))
    embed.set_footer(text='\n'.join(statstat))

    return embed