import discord
import datetime
import json
import asyncio
import platform
import aiomysql
import os
import logging
import logging.handlers
import importlib
import paramiko
from itertools import chain
from utils import errors, checks, msglogger, emojictrl, datamgr, embedmgr
from utils.azalea import Azalea
from db import charsettings, market, regions, permissions, exptable, baseexp, items
from ingame.farming import farm_plants
from templates import azaleaembeds, charembeds, farmembeds, ingameembeds, publicembeds, basecembeds, eventembeds, farmembeds, gameembeds, gamedebugembeds

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

loop = asyncio.get_event_loop()

# SSH Connect
sshclient = paramiko.SSHClient()
sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy)
sshclient.connect(ssh['host'], username=ssh['user'], password=ssh['password'], port=ssh['port'])

async def dbcmd(cmd):
    _, stdout, _ = await client.loop.run_in_executor(None, sshclient.exec_command, cmd)
    lines = stdout.readlines()
    return ''.join(lines)

# DB Connect
dbkey = 'default'
if config['betamode']:
    dbkey = 'beta'

async def connect_db():
    pool = await aiomysql.create_pool(
        host=dbac[dbkey]['host'],
        user=dbac[dbkey]['dbUser'],
        password=dbac[dbkey]['dbPassword'],
        db=dbac[dbkey]['dbName'],
        charset='utf8',
        autocommit=True
    )
    return pool
    
pool = loop.run_until_complete(connect_db())

intents = discord.Intents.all()
client = Azalea(command_prefix=prefixes, error=errors, status=discord.Status.dnd, activity=discord.Game('아젤리아 시작'), intents=intents)
client.remove_command('help')
msglog = msglogger.Msglog(logger)

for i in color.keys(): # convert HEX to DEC
    color[i] = int(color[i], 16)

emj = emojictrl.Emoji(client, emojis['emoji-server'], emojis['emojis'])

# 인게임 DB 로드
def load_items():
    return list(chain.from_iterable([getattr(items, one) for one in items.__all__]))

def loader(datadb: datamgr.DataDB):
    datadb.load_items(load_items())
    datadb.load_char_settings(charsettings.CHAR_SETTINGS)
    datadb.load_region('azalea', regions.REGIONS)
    datadb.load_market('main', market.MARKET)
    datadb.load_permissions(permissions.PERMISSIONS)
    datadb.load_exp_table(exptable.EXP_TABLE)
    datadb.load_farm_plants(farm_plants.PLANTS)
    datadb.load_base_exp(baseexp.BASE_EXP)

def reloader(datadb: datamgr.DataDB):
    db_modules = [
        items,
        charsettings,
        regions,
        market,
        permissions,
        exptable,
        farm_plants,
        baseexp
    ]
    for md in db_modules:
        importlib.reload(md)
    loader(datadb)

datadb = datamgr.DataDB()
datadb.set_loader(loader)
datadb.set_reloader(reloader)
loader(datadb)

embedmgr = embedmgr.EmbedMgr(
    pool,
    azaleaembeds,
    charembeds,
    farmembeds,
    ingameembeds,
    publicembeds,
    basecembeds,
    eventembeds,
    farmembeds,
    gameembeds,
    gamedebugembeds
)

check = checks.Checks(pool, datadb)

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
client.add_data('pool', pool)
client.add_data('embedmgr', embedmgr)
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
if config['inspection']:
    client.add_data('on_inspection', True)
    client.add_check(check.on_inspection)
else:
    client.add_data('on_inspection', False)

client.datas['allexts'] = []
for ext in list(filter(lambda x: x.endswith('.py') and not x.startswith('_'), os.listdir('./exts'))):
    client.datas['allexts'].append('exts.' + os.path.splitext(ext)[0])
    client.load_extension('exts.' + os.path.splitext(ext)[0])
logger.info('{} 개의 확장을 로드했습니다'.format(len(client.datas.get('allexts'))))

client.run(token)