import discord
from discord.ext import commands, tasks
import datetime
import json
import asyncio
import platform
import pymysql
import os
import sys
import logging
import logging.handlers
import traceback
import paramiko
from random import randint
from exts.utils import errors, checks, msglogger, emojictrl, permutil, itemmgr
from exts.utils.azalea import Azalea

# Local Data Load
with open('./data/config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)
with open('./data/version.json', 'r', encoding='utf-8') as version_file:
    version = json.load(version_file)
with open('./data/color.json', 'r', encoding='utf-8') as color_file:
    color = json.load(color_file)
with open('./data/emojis.json', 'r', encoding='utf-8') as emojis_file:
    emojis = json.load(emojis_file)

dbs = {}
for onedb in os.listdir('./db'):
    with open('./db/' + onedb, 'r', encoding='utf-8') as dbfile:
        dbs[os.path.splitext(onedb)[0]] = json.load(dbfile)

print(dbs)

templates = {}
# Load Templates
with open('./templates/baseitem.json', encoding='utf-8') as baseitem_file:
    templates['baseitem'] = json.load(baseitem_file)

# Make Dir
reqdirs = ['./logs', './logs/azalea', './logs/error', './logs/ping']
for dit in reqdirs:
    if not os.path.isdir(dit):
        os.makedirs(dit)

logger = logging.getLogger('azalea')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_streamh = logging.StreamHandler()
log_streamh.setFormatter(log_formatter)
logger.addHandler(log_streamh)
log_fileh = logging.handlers.RotatingFileHandler('./logs/azalea/azalea.log', maxBytes=config['maxlogbytes'], backupCount=10)
log_fileh.setFormatter(log_formatter)
logger.addHandler(log_fileh)

pinglogger = logging.getLogger('ping')
pinglogger.setLevel(logging.INFO)
ping_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ping_fileh = logging.handlers.RotatingFileHandler('./logs/ping/ping.log', maxBytes=config['maxlogbytes'], backupCount=10)
ping_fileh.setFormatter(ping_formatter)
pinglogger.addHandler(ping_fileh)

errlogger = logging.getLogger('error')
errlogger.setLevel(logging.DEBUG)
err_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
err_streamh = logging.StreamHandler()
err_streamh.setFormatter(err_formatter)
errlogger.addHandler(err_streamh)
err_fileh = logging.handlers.RotatingFileHandler('./logs/error/error.log', maxBytes=config['maxlogbytes'], backupCount=10)
err_fileh.setFormatter(err_formatter)
errlogger.addHandler(err_fileh)

logger.info('========== START ==========')

# IMPORTant data
if platform.system() == 'Windows':
    if config['betamode'] == False:
        with open(os.path.abspath(config['securedir']['Windows']) + '\\' + config['tokenFileName'], encoding='utf-8') as token_file:
            token = token_file.read()
    else:
        with open(os.path.abspath(config['securedir']['Windows']) + '\\' + config['betatokenFileName'], encoding='utf-8') as token_file:
            token = token_file.read()
    with open(os.path.abspath(config['securedir']['Windows']) + '\\' + config['dbacName'], encoding='utf-8') as dbac_file:
        dbac = json.load(dbac_file)
    with open(os.path.abspath(config['securedir']['Windows']) + '\\' + config['sshFileName'], encoding='utf-8') as ssh_file:
        ssh = json.load(ssh_file)
elif platform.system() == 'Linux':
    if config['is_android']:
        if config['betamode'] == False:
            with open(os.path.abspath(config['securedir']['Android']) + '/' + config['tokenFileName'], encoding='utf-8') as token_file:
                token = token_file.read()
        else:
            with open(os.path.abspath(config['securedir']['Android']) + '/' + config['betatokenFileName'], encoding='utf-8') as token_file:
                token = token_file.read()
        with open(os.path.abspath(config['securedir']['Android']) + '/' + config['dbacName'], encoding='utf-8') as dbac_file:
            dbac = json.load(dbac_file)
        with open(os.path.abspath(config['securedir']['Android']) + '/' + config['sshFileName'], encoding='utf-8') as ssh_file:
            ssh = json.load(ssh_file)
    else:
        if config['betamode'] == False:
            with open(os.path.abspath(config['securedir']['Linux']) + '/' + config['tokenFileName'], encoding='utf-8') as token_file:
                token = token_file.read()
        else:
            with open(os.path.abspath(config['securedir']['Linux']) + '/' + config['betatokenFileName'], encoding='utf-8') as token_file:
                token = token_file.read()
        with open(os.path.abspath(config['securedir']['Linux']) + '/' + config['dbacName'], encoding='utf-8') as dbac_file:
            dbac = json.load(dbac_file)
        with open(os.path.abspath(config['securedir']['Linux']) + '/' + config['sshFileName'], encoding='utf-8') as ssh_file:
            ssh = json.load(ssh_file)

# SSH Connect
sshclient = paramiko.SSHClient()
sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy)
sshclient.connect(ssh['host'], username=ssh['user'], password=ssh['password'], port=ssh['port'])

async def dbcmd(cmd):
    stdin, stdout, stderr = await client.loop.run_in_executor(None, sshclient.exec_command, cmd)
    lines = stdout.readlines()
    return ''.join(lines)

# DB Connect
dbkey = 'default'
if config['betamode']:
    dbkey = 'beta'

db = pymysql.connect(
    host=dbac[dbkey]['host'],
    user=dbac[dbkey]['dbUser'],
    password=dbac[dbkey]['dbPassword'],
    db=dbac[dbkey]['dbName'],
    charset='utf8',
    autocommit=True
)
cur = db.cursor(pymysql.cursors.DictCursor)

prefix = config['prefix']
client = Azalea(command_prefix=prefix, error=errors, status=discord.Status.dnd, activity=discord.Game('아젤리아 시작'))
client.remove_command('help')
msglog = msglogger.Msglog(logger)

for i in color.keys(): # convert HEX to DEC
    color[i] = int(color[i], 16)

check = checks.Checks(cur=cur)
emj = emojictrl.Emoji(client, emojis['emoji-server'], emojis['emojis'])

gamenum = 0

@client.event
async def on_ready():
    logger.info(f'로그인: {client.user.id}')
    logger.info('백그라운드 루프를 시작합니다.')
    await client.change_presence(status=discord.Status.online)
    pingloop.start()
    if config['betamode']:  
        logger.warning('BETA MODE ENABLED')

@tasks.loop(seconds=5)
async def pingloop():
    try:
        ping = int(client.latency*100000)/100
        if ping <= 100:
            pinglevel = '🔵 매우좋음'
        elif ping <= 300:
            pinglevel = '🟢 양호함'
        elif ping <= 500:
            pinglevel = '🟡 보통'
        elif ping <= 700:
            pinglevel = '🔴 나쁨'
        else:
            pinglevel = '⚪ 매우나쁨'
        client.set_data('ping', (ping, pinglevel))
        pinglogger.info(f'{ping}ms')
        pinglogger.info(f'CLIENT_CONNECTED: {not client.is_closed()}')
        guildshards = {}
        for one in client.latencies:
            guildshards[one[0]] = tuple(filter(lambda guild: guild.shard_id == one[0], client.guilds))
        client.set_data('guildshards', guildshards)
        client.get_data('guildshards')
    except:
        errlogger.error(traceback.format_exc())

@client.event
async def on_error(event, *args, **kwargs):
    ignoreexc = [discord.http.NotFound]
    excinfo = sys.exc_info()
    errstr = f'{"".join(traceback.format_tb(excinfo[2]))}{excinfo[0].__name__}: {excinfo[1]}'
    errlogger.error('\n========== sERROR ==========\n' + errstr + '\n========== sERREND ==========')

@client.event
async def on_command_error(ctx: commands.Context, error: Exception):
    allerrs = (type(error), type(error.__cause__))
    tb = traceback.format_exception(type(error), error, error.__traceback__)
    err = []
    for line in tb:
        err.append(line.rstrip())
    errstr = '\n'.join(err)
    if hasattr(ctx.command, 'on_error'):
        return
    elif commands.errors.MissingRequiredArgument in allerrs:
        return
    elif isinstance(error, errors.NotRegistered):
        await ctx.send(embed=discord.Embed(title='❗ 등록되지 않은 사용자입니다!', description=f'`{prefix}등록` 명령으로 등록해주세요!', color=color['error']))
        msglog.log(ctx, '[미등록 사용자]')
        return
    elif isinstance(error, errors.NotMaster):
        return
    elif errors.ParamsNotExist in allerrs:
        embed = discord.Embed(title=f'❓ 존재하지 않는 명령 옵션입니다: {", ".join(str(error.__cause__.param))}', description=f'`{prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        msglog.log(ctx, '[존재하지 않는 명령 옵션]')
        return
    elif isinstance(error, commands.errors.CommandNotFound):
        embed = discord.Embed(title='❓ 존재하지 않는 명령어입니다!', description=f'`{prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요.', color=color['error'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        msglog.log(ctx, '[존재하지 않는 명령]')
        return
    elif isinstance(error, errors.SentByBotUser):
        return
    elif isinstance(error, commands.errors.NoPrivateMessage):
        embed = discord.Embed(title='⛔ 길드 전용 명령어', description='이 명령어는 길드 채널에서만 사용할 수 있습니다!', color=color['error'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        msglog.log(ctx, '[길드 전용 명령]')
        return
    elif isinstance(error, commands.errors.PrivateMessageOnly):
        embed = discord.Embed(title='⛔ DM 전용 명령어', description='이 명령어는 개인 메시지에서만 사용할 수 있습니다!', color=color['error'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        msglog.log(ctx, '[DM 전용 명령]')
        return
    elif isinstance(error, (commands.errors.CheckFailure, commands.errors.MissingPermissions)):
        perms = [permutil.format_perm_by_name(perm) for perm in error.missing_perms]
        embed = discord.Embed(title='⛔ 멤버 권한 부족!', description=f'{ctx.author.mention}, 이 명령어를 사용하려면 다음과 같은 길드 권한이 필요합니다!\n`' + '`, `'.join(perms) + '`', color=color['error'], timestamp=datetime.datetime.utcnow())
        await ctx.send(embed=embed)
        msglog.log(ctx, '[멤버 권한 부족]')
        return
    elif isinstance(error.__cause__, discord.HTTPException):
        if error.__cause__.code == 50013:
            missings = permutil.find_missing_perms_by_tbstr(errstr)
            fmtperms = [permutil.format_perm_by_name(perm) for perm in missings]
            embed = discord.Embed(title='⛔ 봇 권한 부족!', description='이 명령어를 사용하는 데 필요한 봇의 권한이 부족합니다!\n`' + '`, `'.join(fmtperms) + '`', color=color['error'], timestamp=datetime.datetime.utcnow())
            await ctx.send(embed=embed)
            msglog.log(ctx, '[봇 권한 부족]')
            return
        elif error.__cause__.code == 50035:
            embed = discord.Embed(title='❗ 메시지 전송 실패', description='보내려고 하는 메시지가 너무 길어 전송에 실패했습니다.', color=color['error'], timestamp=datetime.datetime.utcnow())
            await ctx.send(embed=embed)
            msglog.log(ctx, '[너무 긴 메시지 전송 시도]')
            return
        else:
            await ctx.send('오류 코드: ' + str(error.__cause__.code))
    
    errlogger.error('\n========== CMDERROR ==========\n' + errstr + '\n========== CMDERREND ==========')
    embed = discord.Embed(title='❌ 오류!', description=f'무언가 오류가 발생했습니다!\n```python\n{errstr}```\n오류가 기록되었습니다. 나중에 개발자가 확인하고 처리하게 됩니다.', color=color['error'], timestamp=datetime.datetime.utcnow())
    await ctx.send(embed=embed)
    msglog.log(ctx, '[커맨드 오류]')

client.add_check(check.notbot)

client.add_data('config', config)
client.add_data('color', color)
client.add_data('check', check)
client.add_data('emojictrl', emj)
client.add_data('msglog', msglog)
client.add_data('errlogger', errlogger)
client.add_data('logger', logger)
client.add_data('templates', templates)
client.add_data('cur', cur)
client.add_data('dbcmd', dbcmd)
client.add_data('ping', None)
client.add_data('guildshards', None)
client.add_data('version_str', version['versionPrefix'] + version['versionNum'])
client.add_data('lockedexts', ['exts.basecmds'])
client.add_data('dbs', dbs)
client.add_data('start', datetime.datetime.now())

client.datas['allexts'] = []
for ext in list(filter(lambda x: x.endswith('.py'), os.listdir('./exts'))):
    client.datas['allexts'].append('exts.' + os.path.splitext(ext)[0])
    client.load_extension('exts.' + os.path.splitext(ext)[0])

client.run(token)