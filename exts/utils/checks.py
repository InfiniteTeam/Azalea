import discord
from discord.ext import commands
from exts.utils import errors

class Checks:
    def __init__(self, cur):
        self.cur = cur

    def set_cursor(self, cur):
        self.cur = cur

    async def registered(self, ctx: commands.Context):
        if self.cur.execute('select * from userdata where id=%s', ctx.author.id):
            return True
        raise errors.NotRegistered('가입되지 않은 사용자입니다: {}'.format(ctx.author.id))
    
    def is_registered(self):
        return commands.check(self.registered)

    async def master(self, ctx: commands.Context):
        if self.cur.execute('select * from userdata where id=%s and type=%s', (ctx.author.id, 'Master')):
            return True
        raise errors.NotMaster('마스터 유저가 아닙니다: {}'.format(ctx.author.id))

    def is_master(self):
        return commands.check(self.master)

    async def notbot(self, ctx: commands.Context):
        if not ctx.author.bot:
            return True
        raise errors.SentByBotUser('봇 유저로부터 메시지를 받았습니다: {}'.format(ctx.author.id))

    def is_notbot(self):
        return commands.check(self.notbot)