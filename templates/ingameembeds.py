import discord
from discord.ext import commands
import datetime
from dateutil.relativedelta import relativedelta
from exts.utils import pager, timedelta, basecog
from exts.utils.datamgr import DataDB, ItemDBMgr, MarketItem, ItemData, CharMgr, CharacterData, SettingDBMgr, SettingMgr

async def market_embed(datadb: DataDB, pgr: pager.Pager, *, color, mode='default'):
    items = pgr.get_thispage()
    embed = discord.Embed(title='🛍 상점', description='', color=color)
    idgr = ItemDBMgr(datadb)
    for idx in range(len(items)):
        one: MarketItem = items[idx]
        itemdb = idgr.fetch_item(one.item.id)
        enchants = ['`{}` {}'.format(idgr.fetch_enchantment(enc.name).title, enc.level) for enc in one.item.enchantments]
        enchantstr = ''
        if enchants:
            enchantstr = ', '.join(enchants) + '\n'
        if one.discount:
            pricestr = '~~`{}`~~ {} 골드'.format(one.price, one.discount)
        else:
            pricestr = str(one.price) + ' 골드'
        if mode == 'select':
            embed.title += ' - 선택 모드'
            embed.description += str(idx+1) + '. '
        else:
            embed.description += '🔹 '
        embed.description += '**{}**\n{}{}\n\n'.format(itemdb.name, enchantstr, pricestr)
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

async def marketitem_embed(datadb: DataDB, ctx: commands.Context, marketitem: MarketItem, mode='default', *, delete_count: int=0):
    idgr = ItemDBMgr(datadb)
    item = idgr.fetch_item(marketitem.item.id)
    color = ctx.bot.get_data('color')['info']
    embed = discord.Embed(title=item.icon + ' ' + item.name, description=item.description, color=color)
    embed.set_author(name='📔 아이템 상세 정보')
    enchantstr = ''
    for enchant in marketitem.item.enchantments:
        enchantstr += '`{}` {}\n'.format(idgr.fetch_enchantment(enchant.name).title, enchant.level)
    if not enchantstr:
        enchantstr = '없음'
    embed.add_field(name='마법부여', value=enchantstr)
    if marketitem.discount is not None:
        embed.add_field(name='가격', value='~~`{}`~~ {} 골드'.format(marketitem.price, marketitem.discount))
    else:
        embed.add_field(name='가격', value='{} 골드'.format(marketitem.price))
    return embed

async def backpack_embed(cog: basecog.BaseCog, ctx, pgr: pager.Pager, charname, mode='default'):
    items = pgr.get_thispage()
    itemstr = ''
    moneystr = ''
    cmgr = CharMgr(cog.cur)
    char = cmgr.get_character(charname)
    idb = ItemDBMgr(cog.datadb)
    for idx in range(len(items)):
        one = items[idx]
        founditem = idb.fetch_item(one.id)
        icon = founditem.icon
        name = founditem.name
        count = one.count
        if mode == 'select':
            itemstr += '{}. {} **{}** ({}개)\n'.format(idx+1, icon, name, count)
        else:
            itemstr += '{} **{}** ({}개)\n'.format(icon, name, count)
    embed = discord.Embed(
        title=f'💼 `{charname}`의 가방',
        color=cog.color['info']
    )
    moneystr = f'\n**💵 {char.money} 골드**'
    if mode == 'select':
        moneystr = ''
        embed.title += ' - 선택 모드'
    if items:
        embed.description = itemstr + moneystr + '```{}/{} 페이지, 전체 {}개```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
    else:
        embed.description = '\n가방에는 공기 말고는 아무것도 없네요!'
    embed.set_footer(text='❔: 자세히 | 🗑: 버리기')
    return embed

async def char_settings_embed(cog: basecog.BaseCog, pgr: pager.Pager, char: CharacterData, mode='default'):
    sdgr = SettingDBMgr(cog.datadb)
    smgr = SettingMgr(cog.cur, sdgr, char)
    settitles = []
    setvalue = []
    now = pgr.get_thispage()
    for idx in range(len(now)):
        st = now[idx]
        settitles.append(st.title)
        valuestr = str(smgr.get_setting(st.name))
        for x in [('True', '켜짐'), ('False', '꺼짐')]:
            valuestr = valuestr.replace(x[0], x[1])
        setvalue.append(valuestr)
    embed = discord.Embed(title='⚙ `{}` 캐릭터 설정'.format(char.name), color=cog.color['info'])
    if mode == 'select':
        embed.title += ' - 선택 모드'
        embed.add_field(name='번호', value='\n'.join(map(str, range(1, len(now)+1))))
    embed.add_field(name='설정 이름', value='\n'.join(settitles))
    embed.add_field(name='설정값', value='\n'.join(setvalue))
    return embed