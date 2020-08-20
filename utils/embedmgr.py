import discord
from discord.ext import commands
import aiomysql
from utils.basecog import BaseCog
from types import ModuleType
import importlib
from typing import List
from inspect import isclass

class EmbedAlreadyExists(Exception):
    def __init__(self, name):
        super().__init__(f'{name} 임베드 클래스가 이미 존재합니다')
        self.name = name

class EmbedNotFound(Exception):
    pass

class aEmbedBase:
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.cog: BaseCog = ctx.cog

class EmbedMgr:
    def __init__(self, pool: aiomysql.Pool, *modules: ModuleType, default_lang: str='ko'):
        self.pool = pool
        self.modules = list(modules)
        self.default_lang = default_lang
        
    def get_embedclss(self) -> List:
        clss = []
        for m in self.modules:
            for one in dir(m):
                attr = getattr(m, one)
                if isclass(attr) and issubclass(attr, aEmbedBase):
                    if attr in clss:
                        raise EmbedAlreadyExists(attr.__name__)
                    else:
                        clss.append(attr)
        return clss

    async def get(self, ctx: commands.Context, name: str, *args, **kwargs) -> discord.Embed:
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                lang = self.default_lang
                await cur.execute('select lang from userdata where id=%s', ctx.author.id)
                rst = await cur.fetchone()
                if rst is not None:
                    lang = rst['lang']

                embedcls = list(filter(lambda x: x.__name__ == name, self.get_embedclss()))
                if embedcls:
                    embedinstance = embedcls[0](ctx)
                    try:
                        embedfunc = getattr(embedinstance, lang)
                    except AttributeError:
                        embedfunc = getattr(embedinstance, self.default_lang)
                    return await embedfunc(*args, **kwargs)
                raise EmbedNotFound

    async def reload(self):
        for idx, m in enumerate(self.modules):
            self.modules[idx] = importlib.reload(m)

                
