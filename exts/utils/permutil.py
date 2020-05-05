import discord

def format_perm_by_name(name):
    names = {
        'administrator': '관리자',
        'add_reactions': '반응 추가하기'
    }
    try:
        rst = names[name]
    except KeyError:
        rst = name
    return rst

def find_missing_perms_by_tbstr(tbstr: str):
    perms = []
    if 'add_reaction' in tbstr:
        perms.append('add_reactions')
    return perms