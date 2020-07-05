import discord
import datetime
from exts.utils import pager, timedelta
from exts.utils.basecog import BaseCog

async def news_embed(cog: BaseCog, pgr: pager.Pager, *, total: int):
    embed = discord.Embed(title='📰 뉴스', description='', color=cog.color['info'])
    for one in pgr.get_thispage():
        if one.content:
            if one.content.__len__() > 110:
                content = '> ' + one.content[:110] + '...\n'
            else:
                content = '> ' + one.content + '\n'
        else:
            content = ''
        td = datetime.datetime.now() - one.datetime
        if td < datetime.timedelta(minutes=1):
            pubtime = '방금'
        else:
            pubtime = list(timedelta.format_timedelta(td).values())[0] + ' 전'
        embed.description += f'🔹 **`{one.title}`**\n{content}**- {one.company}**, {pubtime}\n\n'
    if total > 40:
        embed.description += '```{}/{} 페이지, 전체 {}건 중 최신 {}건```'.format(pgr.now_pagenum()+1, len(pgr.pages()), total, pgr.objlen())
    else:
        embed.description += '```{}/{} 페이지, 전체 {}건```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
    embed.set_footer(text='* 이 뉴스는 재미 및 게임 플레이를 위한 실제와 상관없는 픽션임을 알려 드립니다.')
    return embed