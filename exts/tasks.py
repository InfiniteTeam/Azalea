import discord
from discord.ext import tasks
import asyncio
import aiomysql
from utils.basecog import BaseCog
from utils import datamgr
import traceback
import datetime
import math
from configs import advlogging
import pylint

# pylint: disable=no-member

class Tasks(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        self.gamenum = 0
        self.last_reset = datetime.datetime.now()
        self.logger.info('백그라운드 루프를 시작합니다.')
        self.sync_guilds.start()
        self.presence_loop.start()
        self.pingloop.start()
        self.delete_char.start()

    def cog_unload(self):
        self.sync_guilds.cancel()
        self.presence_loop.cancel()
        self.pingloop.cancel()
        self.delete_char.cancel()

    @tasks.loop(seconds=5)
    async def pingloop(self):
        try:
            ping = int(self.client.latency*100000)/100
            if ping <= 100:
                pinglevel = 0
            elif ping <= 300:
                pinglevel = 1
            elif ping <= 500:
                pinglevel = 2
            elif ping <= 700:
                pinglevel = 3
            else:
                pinglevel = 4
            self.client.set_data('ping', (ping, pinglevel))
            self.pinglogger.info(f'{ping}ms')
            self.pinglogger.info(f'CLIENT_CONNECTED: {not self.client.is_closed()}')
            guildshards = {}
            if self.client.shard_id:
                for one in self.client.latencies:
                    guildshards[one[0]] = tuple(filter(lambda guild: guild.shard_id == one[0], self.client.guilds))
            self.client.set_data('guildshards', guildshards)
        except:
            self.errlogger.error(traceback.format_exc())

    @tasks.loop(seconds=5)
    async def sync_guilds(self):
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute('select id from serverdata')
                    db_guilds = await cur.fetchall()
                    db_guild_ids = list(map(lambda one: one['id'], db_guilds))
                    client_guild_ids = list(map(lambda one: one.id, self.client.guilds))
                    
                    # 등록 섹션
                    added_ids = list(set(client_guild_ids) - set(db_guild_ids))
                    added = list(map(lambda one: self.client.get_guild(one), added_ids))
                    async def add_guild(guild: discord.Guild):
                        self.logger.info(f'새 서버를 발견했습니다: {guild.name}({guild.id})')
                        sendables = list(filter(lambda ch: ch.permissions_for(guild.me).send_messages, guild.text_channels))
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
                                elif 'announce' in sname:
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
                            await cur.execute('insert into serverdata(id, noticechannel, master) values (%s, %s, %s)', (guild.id, sendables[0].id, 0))
                            self.logger.info(f'서버 추가 성공: ' + guild.name + f'({guild.id})')
                            embed = discord.Embed(title='🎉 안녕하세요!', description=f'안녕하세요! Azalea을 초대해 주셔서 감사합니다. `{self.prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요!', color=self.color['primary'])
                            embed.set_footer(text=f"혹시 이 채널이 공지 채널이 아닌가요? '{self.prefix}공지채널' 명령으로 선택하세요!\n")
                            await sendables[0].send(embed=embed)
                            async def send_log(channel_id: int):
                                channel = self.client.get_channel(channel_id)
                                await channel.send(embed=discord.Embed(title='{} 새 서버를 추가했습니다'.format(self.emj.get(None, 'check')), description='{g}({g.id})'.format(g=guild), color=self.color['info']))
                            aws = []
                            for cid in advlogging.IO_LOG_CHANNEL_IDS:
                                aws.append(send_log(cid))
                            asyncio.gather(*aws)
                        else:
                            await cur.execute('insert into serverdata(id, noticechannel, master) values (%s, %s, %s)', (guild.id, None, 0))
                            self.logger.info(f'접근 가능한 채널이 없는 서버 추가 성공: ' + guild.name + f'({guild.id})')
                            async def send_log(channel_id: int):
                                channel = self.client.get_channel(channel_id)
                                await channel.send(embed=discord.Embed(title='{} 새 서버를 추가했습니다'.format(self.emj.get(None, 'check')), description='{g}({g.id})\n(접근 가능한 채널 없음)'.format(g=guild), color=self.color['info']))
                            aws = []
                            for cid in advlogging.IO_LOG_CHANNEL_IDS:
                                aws.append(send_log(cid))
                            asyncio.gather(*aws)

                    addlist = []
                    for guild in added:
                        addlist.append(add_guild(guild))
                    
                    await asyncio.gather(*addlist)

                    # 제거 섹션
                    deleted_ids = list(set(db_guild_ids) - set(client_guild_ids))
                    async def del_guild(gid: int):
                        self.logger.info(f'존재하지 않는 서버를 발견했습니다: {gid}')
                        await cur.execute('delete from serverdata where id=%s', gid)
                        async def send_log(channel_id: int):
                            channel = self.client.get_channel(channel_id)
                            await channel.send(embed=discord.Embed(title='{} 존재하지 않거나 나간 서버를 발견했습니다'.format(self.emj.get(None, 'cross')), description=f'DB에서 제거했습니다\nID: `{gid}`', color=self.color['info']))
                        aws = []
                        for cid in advlogging.IO_LOG_CHANNEL_IDS:
                            aws.append(send_log(cid))
                        asyncio.gather(*aws)

                    dellist = []
                    for gid in deleted_ids:
                        dellist.append(del_guild(gid))

                    await asyncio.gather(*dellist)

        except:
            self.client.get_data('errlogger').error(traceback.format_exc())

    @tasks.loop(seconds=5)
    async def presence_loop(self):
        try:
            if self.client.get_data('shutdown_left') is not None:
                await self.client.change_presence(
                    activity=discord.Game(
                        str(math.trunc(self.client.get_data('shutdown_left'))) + '초 후 종료'
                    )
                )
            elif self.client.get_data('on_inspection') == True:
                await self.client.change_presence(
                    status=discord.Status.idle,
                    activity=discord.Game(
                        'Azalea 점검 중'
                    )
                )
            else:
                games = [
                    f'〔{self.prefix} 도움〕 입력!',
                    f'{self.prefix} 도움 | {len(self.client.guilds)} 서버',
                    f'{self.prefix} 도움 | {len(self.client.users)} 사용자'
                ]
                await self.client.change_presence(status=discord.Status.online, activity=discord.Game(games[self.gamenum]))
                if self.gamenum == len(games)-1:
                    self.gamenum = 0
                else:
                    self.gamenum += 1
        except:
            self.errlogger.error(traceback.format_exc())

    @tasks.loop(seconds=10)
    async def delete_char(self):
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute('select * from chardata where delete_request is not NULL')
                    delreqs = await cur.fetchall()
                    delnow = list(filter(lambda x: (datetime.datetime.now() - x['delete_request']) > datetime.timedelta(hours=24), delreqs))
                    for one in delnow:
                        cmgr = datamgr.CharMgr(self.pool)
                        await cmgr.delete_character(one['uuid'])
                        self.logger.info('{}({}) 의 "{}"캐릭터가 예약된 시간이 지나 잊혀졌습니다.'.format(self.client.get_user(one['id']), one['id'], one['name']))
        except:
            self.errlogger.error(traceback.format_exc())

    @pingloop.before_loop
    @sync_guilds.before_loop
    @presence_loop.before_loop
    @delete_char.before_loop
    async def before_loop(self):
        await self.client.wait_until_ready()

def setup(client):
    cog = Tasks(client)
    client.add_cog(cog)