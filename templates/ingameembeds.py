import discord
from discord.ext import commands
import datetime
from dateutil.relativedelta import relativedelta
from exts.utils import pager, timedelta
from exts.utils.datamgr import DataDB, ItemDBMgr, MarketItem, ItemData

async def market_embed(datadb: DataDB, pgr: pager.Pager, *, color, mode='default'):
    items = pgr.get_thispage()
    embed = discord.Embed(title='🛍 상점', description='', color=color)
    idgr = ItemDBMgr(datadb)
    for idx in range(len(items)):
        one: MarketItem = items[idx]
        itemdb = idgr.fetch_item(one.item.id)
        enchants = ''
        if one.discount:
            pricestr = '~~`{}`~~ {} 골드'.format(one.price, one.discount)
        else:
            pricestr = str(one.price) + ' 골드'
        embed.description += '🔹 **{}**\n{}{}\n\n'.format(itemdb.name, enchants, pricestr)
    embed.description += '```{}/{} 페이지, 전체 {}개```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
    embed.set_footer(text='💎: 구매 | 💰: 판매 | ❔ 자세히')
    return embed

async def char_embed(username, pgr: pager.Pager, *, color, mode='default'):
    chars = pgr.get_thispage()
    charstr = ''
    for idx in range(len(chars)):
        one = chars[idx]
        name = one.name
        if mode == 'select':
            name = f'{idx+1}. {name}'
        level = one.level
        chartype = one.type.value
        online = one.online
        onlinestr = ''
        if online:
            onlinestr = '(**현재 플레이중**)'
        deleteleftstr = ''
        if one.delete_request:
            tdleft = timedelta.format_timedelta((one.delete_request + relativedelta(hours=24)) - datetime.datetime.now())
            deleteleft = ' '.join(tdleft.values())
            deleteleftstr = '\n**`{}` 후에 삭제됨**'.format(deleteleft)
        charstr += '**{}** {}\n레벨: `{}` \\| 직업: `{}` {}\n\n'.format(name, onlinestr, level, chartype, deleteleftstr)
    embed = discord.Embed(
        title=f'🎲 `{username}`님의 캐릭터 목록',
        description=charstr,
        color=color
    )
    embed.description = charstr + '```{}/{} 페이지, 전체 {}캐릭터```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
    return embed

async def itemdata_embed(datadb: DataDB, ctx: commands.Context, itemdata: ItemData, mode='default', *, delete_count: int=0):
    idgr = ItemDBMgr(datadb)
    item = idgr.fetch_item(itemdata.id)
    color = ctx.bot.get_data('color')['info']
    if mode == 'delete':
        color = ctx.bot.get_data('color')['warn']
    embed = discord.Embed(title=item.icon + ' ' + item.name, description=item.description, color=color)
    embed.set_author(name='📔 아이템 상세 정보')
    enchantstr = ''
    for enchant in itemdata.enchantments:
        enchantstr += '{}: {}\n'.format(enchant.name, enchant.level)
    if not enchantstr:
        enchantstr = '없음'
    embed.add_field(name='마법부여', value=enchantstr)
    if mode == 'delete':
        embed.description = '**정말 이 아이템을 버릴까요? 다시 회수할 수 없습니다.**' + embed.description
        embed.set_author(name='⚠ 아이템 버리기 경고')
        embed.add_field(name='버릴 개수', value='{}개'.format(delete_count))
    else:
        embed.add_field(name='개수', value='{}개'.format(itemdata.count))
    return embed