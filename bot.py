import discord
from discord.ext import commands, tasks
import datetime
import json
import asyncio
import platform
import pymysql
import os
import io
import sys
import logging
import logging.handlers
import traceback
import paramiko
from random import randint
from exts.utils import errors, checks, msglogger, emojictrl, permutil, datamgr
from exts.utils.azalea import Azalea
from ingame.db import enchantments, items, charsettings, market, regions, permissions

# Local Data Load
with open('./data/config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)
with open('./data/version.json', 'r', encoding='utf-8') as version_file:
    version = json.load(version_file)
with open('./data/color.json', 'r', encoding='utf-8') as color_file:
    color = json.load(color_file)
with open('./data/emojis.json', 'r', encoding='utf-8') as emojis_file:
    emojis = json.load(emojis_file)
with open('./data/prefixes.json', 'r', encoding='utf-8') as prefixes_file:
    prefixes = json.load(prefixes_file)['prefixes']
    prefix = prefixes[0]

templates = {}
# Load Templates
with open('./templates/baseitem.json', encoding='utf-8') as tpltfile:
    templates['baseitem'] = json.load(tpltfile)
with open('./templates/basestat.json', encoding='utf-8') as tpltfile:
    templates['basestat'] = json.load(tpltfile)

# Make Dir
reqdirs = ['./logs', './logs/azalea', './logs/error', './logs/ping', './logs/discord']
for dit in reqdirs:
    if not os.path.isdir(dit):
        os.makedirs(dit)

logger = logging.getLogger('azalea')
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_streamh = logging.StreamHandler()
log_streamh.setFormatter(log_formatter)
logger.addHandler(log_streamh)
log_fileh = logging.handlers.RotatingFileHandler('./logs/azalea/azalea.log', maxBytes=config['maxlogbytes'], backupCount=10, encoding='utf-8')
log_fileh.setFormatter(log_formatter)
logger.addHandler(log_fileh)

dlogger = logging.getLogger('discord')
dlogger.setLevel(logging.INFO)
dhandler = logging.handlers.RotatingFileHandler(filename='./logs/discord/discord.log', maxBytes=config['maxlogbytes'], backupCount=10, encoding='utf-8')
dformatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s: %(message)s')
dlog_streamh = logging.StreamHandler()
dhandler.setFormatter(dformatter)
dlog_streamh.setFormatter(dformatter)
dlogger.addHandler(dhandler)
dlogger.addHandler(dlog_streamh)

pinglogger = logging.getLogger('ping')
pinglogger.setLevel(logging.INFO)
ping_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ping_fileh = logging.handlers.RotatingFileHandler('./logs/ping/ping.log', maxBytes=config['maxlogbytes'], backupCount=10, encoding='utf-8')
ping_fileh.setFormatter(ping_formatter)
pinglogger.addHandler(ping_fileh)

errlogger = logging.getLogger('error')
errlogger.setLevel(logging.DEBUG)
err_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
err_streamh = logging.StreamHandler()
err_streamh.setFormatter(err_formatter)
errlogger.addHandler(err_streamh)
err_fileh = logging.handlers.RotatingFileHandler('./logs/error/error.log', maxBytes=config['maxlogbytes'], backupCount=10, encoding='utf-8')
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

sqldb = pymysql.connect(
    host=dbac[dbkey]['host'],
    user=dbac[dbkey]['dbUser'],
    password=dbac[dbkey]['dbPassword'],
    db=dbac[dbkey]['dbName'],
    charset='utf8',
    autocommit=True
)
cur = sqldb.cursor(pymysql.cursors.DictCursor)

client = Azalea(command_prefix=prefixes, error=errors, status=discord.Status.dnd, activity=discord.Game('아젤리아 시작'))
client.remove_command('help')
msglog = msglogger.Msglog(logger)

for i in color.keys(): # convert HEX to DEC
    color[i] = int(color[i], 16)

emj = emojictrl.Emoji(client, emojis['emoji-server'], emojis['emojis'])

# 인게임 DB 로드
datadb = datamgr.DataDB()
datadb.load_enchantments(enchantments.ENCHANTMENTS)
datadb.load_items(items.ITEMS)
datadb.load_char_settings(charsettings.CHAR_SETTINGS)
datadb.load_region('azalea', regions.REGIONS)
datadb.load_market('main', market.MARKET)
datadb.load_permissions(permissions.PERMISSIONS)

check = checks.Checks(cur, datadb)

print(datadb.items)

def awaiter(coro):
    return asyncio.ensure_future(coro)

client.add_check(check.notbot)

# 데이터 적재

client.add_data('config', config)
client.add_data('color', color)
client.add_data('check', check)
client.add_data('emojictrl', emj)
client.add_data('msglog', msglog)
client.add_data('errlogger', errlogger)
client.add_data('pinglogger', pinglogger)
client.add_data('logger', logger)
client.add_data('templates', templates)
client.add_data('dbconn', sqldb)
client.add_data('cur', cur)
client.add_data('dbcmd', dbcmd)
client.add_data('ping', None)
client.add_data('shutdown_left', None)
client.add_data('guildshards', None)
client.add_data('version_str', version['versionPrefix'] + version['versionNum'])
client.add_data('lockedexts', ['exts.basecmds'])
client.add_data('datadb', datadb)
client.add_data('awaiter', awaiter)
client.add_data('eventcogname', 'Events')
client.add_data('start', datetime.datetime.now())

client.datas['allexts'] = []
for ext in list(filter(lambda x: x.endswith('.py'), os.listdir('./exts'))):
    client.datas['allexts'].append('exts.' + os.path.splitext(ext)[0])
    client.load_extension('exts.' + os.path.splitext(ext)[0])

client.run(token)