import discord
from discord.ext import commands
import datetime
from dateutil.relativedelta import relativedelta
from utils import pager, timedelta, basecog
from utils.datamgr import DataDB, ItemDBMgr, MarketItem, ItemData, CharMgr, CharacterData, SettingDBMgr, SettingMgr, MarketDBMgr, StatMgr, ExpTableDBMgr, ItemMgr
from utils.embedmgr import aEmbedBase, aMsgBase

def market_embed(datadb: DataDB, pgr: pager.Pager, *, color, mode='default') -> discord.Embed:
    items = pgr.get_thispage()
    embed = discord.Embed(title='🛍 상점', description='', color=color)
    idgr = ItemDBMgr(datadb)
    for idx, one in enumerate(items):
        itemdb = idgr.fetch_item(one.item.id)
        enchants = ['`{}` {}'.format(idgr.fetch_enchantment(enc.name).title, enc.level) for enc in one.item.enchantments]
        enchantstr = ''
        if enchants:
            enchantstr = ', '.join(enchants) + '\n'
        if one.discount:
            pricestr = '~~`{:n}`~~ {:n} 골드'.format(one.price, one.discount)
        else:
            pricestr = format(one.price, ',') + ' 골드'
        if mode == 'select':
            embed.title += ' - 선택 모드'
            embed.description += f'**{idx+1}.** '
        embed.description += '{} **{}**\n{}{}\n\n'.format(itemdb.icon, itemdb.name, enchantstr, pricestr)
    embed.description += '```{}/{} 페이지, 전체 {}개```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
    embed.set_footer(text='💎: 구매 | 💰: 판매 | ❔ 자세히')
    return embed

async def itemdata_embed(cog: basecog.BaseCog, itemdata: ItemData, mode='default', *, count: int=0, charuuid: str=None) -> discord.Embed:
    idgr = ItemDBMgr(cog.datadb)
    item = idgr.fetch_item(itemdata.id)
    color = cog.color['info']
    if mode == 'delete':
        color = cog.color['warn']
    embed = discord.Embed(title=item.icon + ' ' + item.name, description=item.description, color=color)
    enchantstr = ''
    for enchant in itemdata.enchantments:
        enchantstr += '`{}` {}\n'.format(idgr.fetch_enchantment(enchant.name).title, enchant.level)
    if not enchantstr:
        enchantstr = '없음'
    if mode == 'delete':
        embed.description = '**정말 이 아이템을 버릴까요? 다시 회수할 수 없어요.**'
        embed.add_field(name='아이템 설명', value=item.description)
        embed.set_author(name='⚠ 아이템 버리기 경고')
        embed.add_field(name='버릴 개수', value='{}개'.format(count))
    elif mode == 'sell':
        embed.description = '**다음과 같이 판매할까요? 다시 취소할 수 없어요.**'
        embed.add_field(name='아이템 설명', value=item.description)
        embed.set_author(name='💰 아이템 판매하기')
    else:
        embed.set_author(name='📔 아이템 상세 정보')
        embed.add_field(name='개수', value='{}개'.format(itemdata.count))
    embed.add_field(name='마법부여', value=enchantstr)
    if mode == 'sell':
        imgr = ItemMgr(cog.pool, charuuid)
        money = await imgr.fetch_money()
        embed.add_field(name='최종 판매', value='{:n} 골드 × {:n} 개\n= **{:n} 골드**'.format(idgr.get_final_price(itemdata), count, idgr.get_final_price(itemdata, count)))
        embed.add_field(name='판매 후 잔고', value='{:n} 골드\n↓\n{:n} 골드'.format(money, money + idgr.get_final_price(itemdata, count)))
    return embed

def marketitem_embed(cog: basecog.BaseCog, marketitem: MarketItem, mode='default', *, count: int=0, chardata: CharacterData=None) -> discord.Embed:
    idgr = ItemDBMgr(cog.datadb)
    item = idgr.fetch_item(marketitem.item.id)
    embed = discord.Embed(title=item.icon + ' ' + item.name, description=item.description, color=cog.color['info'])
    enchantstr = ''
    for enchant in marketitem.item.enchantments:
        enchantstr += '`{}` {}\n'.format(idgr.fetch_enchantment(enchant.name).title, enchant.level)
    if not enchantstr:
        enchantstr = '없음'
    if mode == 'buy':
        embed.set_author(name='💎 아이템 구매하기')
        embed.description = '정말 이 아이템을 구매할까요? 환불은 할 수 없어요.'
        embed.add_field(name='아이템 설명', value=item.description)
        if marketitem.discount is not None:
            embed.add_field(name='최종 가격', value='~~`{:n}`~~ {:n} 골드 × {:n} 개\n= **{:n} 골드**'.format(marketitem.price, marketitem.discount, count, marketitem.discount*count))
            embed.add_field(name='구매 후 잔고', value='{:n} 골드\n↓\n{:n} 골드'.format(chardata.money, chardata.money - marketitem.discount*count))
        else:
            embed.add_field(name='최종 가격', value='{:n} 골드 × {:n} 개 = {:n} 골드'.format(marketitem.price, count, marketitem.price*count))
            embed.add_field(name='구매 후 잔고', value='{:n} 골드\n↓\n{:n} 골드'.format(chardata.money, chardata.money - marketitem.price*count))
    else:
        embed.set_author(name='📔 아이템 상세 정보')
        if marketitem.discount is not None:
            embed.add_field(name='가격', value='~~`{:n}`~~ {:n} 골드'.format(marketitem.price, marketitem.discount))
        else:
            embed.add_field(name='가격', value='{:n} 골드'.format(marketitem.price))
    embed.add_field(name='마법부여', value=enchantstr)
    return embed

class Backpack(aEmbedBase):
    async def ko(self, pgr: pager.Pager, charuuid, mode='default'):
        items = pgr.get_thispage()
        itemstr = ''
        moneystr = ''
        cmgr = CharMgr(self.cog.pool)
        char = await cmgr.get_character(charuuid)
        imgr = ItemDBMgr(self.cog.datadb)
        idgr = ItemDBMgr(self.cog.datadb)
        for idx, one in enumerate(items):
            founditem = idgr.fetch_item(one.id)
            icon = founditem.icon
            name = founditem.name
            count = one.count
            enchants = []
            for enc in one.enchantments:
                enchants.append('`{}` {}'.format(imgr.fetch_enchantment(enc.name).title, enc.level))
            enchantstr = ''
            if enchants:
                enchantstr = '> ' + ", ".join(enchants) + '\n'
            if mode == 'select':
                itemstr += '{}. {} **{}** ({}개)\n{}'.format(idx+1, icon, name, count, enchantstr)
            else:
                itemstr += '{} **{}** ({}개)\n{}'.format(icon, name, count, enchantstr)
        embed = discord.Embed(
            title=f'💼 `{char.name}`의 가방',
            color=self.cog.color['info']
        )
        moneystr = f'\n**💵 {char.money:n} 골드**'
        if mode == 'select':
            moneystr = ''
            embed.title += ' - 선택 모드'
        if items:
            embed.description = itemstr + moneystr + '```{}/{} 페이지, 전체 {}개```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
            embed.set_footer(text='❔: 자세히 | 🗑: 버리기')
        else:
            embed.description = '\n가방에는 공기 말고는 아무것도 없네요!\n' + moneystr
        return embed


def backpack_sell_embed(cog: basecog.BaseCog, ctx, pgr: pager.Pager, charname, mode='select') -> discord.Embed:
    items = pgr.get_thispage()
    itemstr = ''
    imgr = ItemDBMgr(cog.datadb)
    idgr = ItemDBMgr(cog.datadb)
    for idx, one in enumerate(items):
        founditem = idgr.fetch_item(one.id)
        icon = founditem.icon
        name = founditem.name
        count = one.count
        enchants = []
        for enc in one.enchantments:
            enchants.append('`{}` {}'.format(imgr.fetch_enchantment(enc.name).title, enc.level))
        enchantstr = ''
        if enchants:
            enchantstr = '> ' + ", ".join(enchants) + '\n'
        itemstr += '{}. {} **{}** ({}개): `{:n}` 골드\n{}'.format(idx+1, icon, name, count, idgr.get_final_price(one), enchantstr)
    embed = discord.Embed(
        title=f'💼 `{charname}`의 가방 - 선택 모드',
        color=cog.color['info']
    )
    embed.set_author(name='💰 아이템 판매 - 아이템 선택')
    embed.set_footer(text='⚠ 판매 가능한 아이템만 표시됩니다')
    if items:
        embed.description = itemstr + '```{}/{} 페이지, 전체 {}개```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
    else:
        embed.description = '\n가방에는 공기 말고는 아무것도 없네요!'
    return embed

def rank_embed(cog: basecog.BaseCog, pgr: pager.Pager, *, orderby='money', where='server', guild: discord.Guild=None) -> discord.Embed:
    if orderby == 'money':
        orderby_str = '재산'
    if where == 'server':
        where_str = '서버'
        embed = discord.Embed(title='🏆 Azalea {} {} 랭킹'.format(orderby_str, where_str), description='', color=cog.color['info'])
    elif where == 'global':
        where_str = '전체'
        embed = discord.Embed(title='🌏 Azalea {} {} 랭킹'.format(orderby_str, where_str), description='', color=cog.color['info'])
    now = pgr.get_thispage()
    for idx, char in enumerate(now, pgr.start_number_now()+1):
        if idx == 1:
            idxstr = '🥇'
        elif idx == 2:
            idxstr = '🥈'
        elif idx == 3:
            idxstr = '🥉'
        else:
            idxstr = f'{idx}.'
        if where == 'server':
            embed.description +='{} **{}**\n> 💵 `{}`, {}\n\n'.format(idxstr, char.name, char.money, guild.get_member(char.id).mention)
        elif where == 'global':
            embed.description +='{} **{}**\n> 💵 `{}`, {}\n\n'.format(idxstr, char.name, char.money, cog.client.get_user(char.id).name)
    embed.description += '```{}/{} 페이지, 전체 {}개```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
    return embed