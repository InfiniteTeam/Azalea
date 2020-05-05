import discord
from discord.ext import commands, tasks
from exts.utils.basecog import BaseCog
import traceback

# pylint: disable=no-member

class Tasks(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.gamenum = 0
        self.sync_guilds.start()
        self.presence_loop.start()

    def cog_unload(self):
        self.sync_guilds.cancel()
        self.presence_loop.cancel()

    @tasks.loop(seconds=5)
    async def sync_guilds(self):
        try:
            self.cur.execute('select id from serverdata')
            db_guilds = self.cur.fetchall()
            db_guild_ids = list(map(lambda one: one['id'], db_guilds))
            client_guild_ids = list(map(lambda one: one.id, self.client.guilds))
            
            # 등록 섹션
            added_ids = list(set(client_guild_ids) - set(db_guild_ids))
            added = list(map(lambda one: self.client.get_guild(one), added_ids))
            for guild in added:
                self.logger.info(f'새 서버를 발견했습니다: {guild.name}({guild.id})')
                sendables = list(filter(lambda ch: ch.permissions_for(guild.get_member(self.client.user.id)).send_messages, guild.text_channels))
                if sendables:
                    selected = []
                    for sch in sendables:
                        sname = sch.name.lower()
                        if '공지' in sname and '봇' in sname:
                            pass
                        elif 'noti' in sname and 'bot' in sname:
                            pass

                        elif '공지' in sname:
                            pass
                        elif 'noti' in sname:
                            pass

                        elif '봇' in sname:
                            pass
                        elif 'bot' in sname:
                            pass

                        else:
                            continue
                        selected.append(sch)
                    
                    if not selected:
                        selected.append(sendables[0])
                    self.cur.execute('insert into serverdata(id, noticechannel, master) values (%s, %s, %s)', (guild.id, sendables[0].id, 0))
                    self.logger.info(f'서버 추가 성공: ' + guild.name + f'({guild.id})')
                    embed = discord.Embed(title='🎉 안녕하세요!', description=f'안녕하세요! Azalea을 초대해 주셔서 감사합니다. `{self.client.command_prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요!\n혹시 이 채널이 공지 채널이 아닌가요? `{self.client.command_prefix}공지채널` 명령으로 선택하세요!', color=self.color['primary'])
                    await sendables[0].send(embed=embed)
                else:
                    self.cur.execute('insert into serverdata(id, noticechannel, master) values (%s, %s, %s)', (guild.id, None, 0))
                    self.logger.info(f'접근 가능한 채널이 없는 서버 추가 성공: ' + guild.name + f'({guild.id})')
            # 제거 섹션
            deleted_ids = list(set(db_guild_ids) - set(client_guild_ids))
            for gid in deleted_ids:
                self.logger.info(f'존재하지 않는 서버를 발견했습니다: {gid}')
                self.cur.execute('delete from serverdata where id=%s', gid)

        except:
            self.client.get_data('errlogger').error(traceback.format_exc())

    @sync_guilds.before_loop
    async def b_register_guilds(self):
        await self.client.wait_until_ready()

    @tasks.loop(seconds=7)
    async def presence_loop(self):
        try:
            games = [f'{self.client.command_prefix}개발중...', f'{len(self.client.guilds)}개의 서버와 함께', f'{len(self.client.users)}명의 사용자와 함께']
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game(games[self.gamenum]))
            if self.gamenum == len(games)-1:
                self.gamenum = 0
            else:
                self.gamenum += 1
        except:
            self.errlogger.error(traceback.format_exc())

    @presence_loop.before_loop
    async def b_presence_loop(self):
        await self.client.wait_until_ready()

def setup(client):
    cog = Tasks(client)
    client.add_cog(cog)