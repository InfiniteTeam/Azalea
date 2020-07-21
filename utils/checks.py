import discord
from discord.ext import commands
import aiomysql
from . import errors, datamgr
from .dbtool import DB

class Checks:
    def __init__(self, pool: aiomysql.Pool, datadb: datamgr.DataDB):
        self.pool = pool
        self.datadb = datadb

    async def registered(self, ctx: commands.Context):
        async with DB(self.pool) as db:
            cur = db.cur
            if await cur.execute('select * from userdata where id=%s', ctx.author.id) != 0:
                return True
            raise errors.NotRegistered('가입되지 않은 사용자입니다: {}'.format(ctx.author.id))
    
    def is_registered(self):
        return commands.check(self.registered)

    async def master(self, ctx: commands.Context):
        async with DB(self.pool) as db:
            cur = db.cur
            if not ctx.guild:
                raise commands.NoPrivateMessage('관리자 명령어는 DM에서 사용할 수 없습니다')
            if await cur.execute('select * from userdata where id=%s and type=%s', (ctx.author.id, 'Master')) != 0 and await cur.execute('select * from serverdata where id=%s and master=%s', (ctx.guild.id, True)) != 0:
                return True
            raise errors.NotMaster('마스터 유저가 아닙니다: {}'.format(ctx.author.id))

    def is_master(self):
        return commands.check(self.master)

    def has_azalea_permissions(self, **perms: bool):
        async def predicate(ctx: commands.Context):
            async with DB(self.pool) as db:
                cur = db.cur
                await cur.execute('select * from userdata where id=%s', ctx.author.id)
                fetch = await cur.fetchone()
                value = fetch['perms']
                pdgr = datamgr.PermDBMgr(self.datadb)
                master = pdgr.get_permission('master').value
                if (value & master) == master:
                    return True
                missings = []
                for one in perms:
                    perm = pdgr.get_permission(one)
                    if perms[one]:
                        if (value & perm.value) == perm.value:
                            continue
                    else:
                        if (value & perm.value) != perm.value:
                            continue
                    missings.append(perm.name)
                    raise errors.MissingAzaleaPermissions(missings)
                return True
            
        return predicate

    async def notbot(self, ctx: commands.Context):
        if not ctx.author.bot:
            return True
        raise errors.SentByBotUser('봇 유저로부터 메시지를 받았습니다: {}'.format(ctx.author.id))

    def is_notbot(self):
        return commands.check(self.notbot)

    async def char_online(self, ctx: commands.Context):
        async with DB(self.pool) as db:
            cur = db.cur
            if await cur.execute('select * from chardata where id=%s and online=%s', (ctx.author.id, True)) != 0:
                return True
            raise errors.NoCharOnline('로그인된 캐릭터가 없습니다')

    def if_char_online(self):
        return commands.check(self.char_online)

    async def subcmd_vaild(self, ctx: commands.Context):
        cnames = list(map(lambda cmd: cmd.name, ctx.command.commands)) + [None]
        if ctx.subcommand_passed in cnames:
            return True
        raise commands.CommandNotFound

    def if_subcmd_vaild(self):
        return commands.check(self.subcmd_vaild)

    async def on_inspection(self, ctx: commands.Context):
        try:
            result = await self.master(ctx)
        except errors.NotMaster:
            raise errors.onInspection('점검 중에는 마스터 유저만 사용이 가능합니다')
        else:
            return result