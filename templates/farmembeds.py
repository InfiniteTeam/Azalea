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
    garo = round(math.sqrt(area))
    sero = area // garo
    namuji = area - garo * sero

    plants = await farm_mgr.get_plants()

    statstr = ''
    loops = 0

    def plus():
        nonlocal plants, statstr, loops
        if len(plants) > loops:
            if plants[loops].status == FarmPlantStatus.AllGrownUp:
                statstr += '🟧'
            elif plants[loops].status == FarmPlantStatus.Growing:
                statstr += '🟨'
            elif plants[loops].status == FarmPlantStatus.Sprouted:
                statstr += '🟩'
            elif plants[loops].status == FarmPlantStatus.Planted:
                statstr += '⬜'

    for x in range(sero):
        for y in range(garo):
            plus()
            statstr += '\n'
            loops += 1
    for z in range(namuji):
        plus()
        loops += 1

    embed = discord.Embed(title=f'🌱 `{char.name}` 의 농장 상태', color=cog.color['info'])
    embed.add_field(name='작물 성장 상태', value=statstr)
    embed.set_footer(text='🟫: 빈 땅')

    return embed