import discord
from utils.basecog import BaseCog
from utils.mgrerrors import CharCreateError, CharCreateErrReasons
from utils import pager, timedelta
from utils.datamgr import StatMgr, ExpTableDBMgr
import datetime
from dateutil.relativedelta import relativedelta

async def char_embed(cog, username, pgr: pager.Pager, *, mode='default') -> discord.Embed:
    edgr = ExpTableDBMgr(cog.datadb)
    chars = pgr.get_thispage()
    charstr = ''
    for idx, one in enumerate(chars):
        name = one.name
        samgr = StatMgr(cog.pool, one.uid)
        if mode == 'select':
            name = f'{idx+1}. {name}'
        level = await samgr.get_level(edgr)
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
        color=cog.color['info']
    )
    embed.description = charstr + '```{}/{} 페이지, 전체 {}캐릭터```'.format(pgr.now_pagenum()+1, len(pgr.pages()), pgr.objlen())
    embed.set_footer(text='✨: 새로 만들기 | 🎲: 캐릭터 변경 | ❔: 캐릭터 정보')
    return embed

def charcreate_fail_embed(cog: BaseCog, exc: CharCreateError):
    if exc.reason == CharCreateErrReasons.InvalidName:
        embed = discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='캐릭터 이름은 반드시 한글, 영어, 숫자만을 사용해야 합니다.\n다시 시도해 주세요!', color=cog.color['error'])
        return embed
    elif exc.reason == CharCreateErrReasons.InvalidLength:
        embed = discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='캐릭터 이름은 2~10글자이여야 합니다.\n다시 시도해 주세요!', color=cog.color['error'])
        return embed
    elif exc.reason == CharCreateErrReasons.NameAlreadyExists:
        embed = discord.Embed(title='❌ 이미 사용중인 이름입니다!', description='다시 시도해 주세요!', color=cog.color['error'])
        return embed
    else:
        exc.reason == CharCreateErrReasons.CannotIncludePrefix
        embed = discord.Embed(title='❌ 사용할 수 없는 이름입니다!', description='아젤리아 봇 접두사는 이름에 포함할 수 없습니다.\n다시 시도해 주세요!', color=cog.color['error'])
        return embed
    