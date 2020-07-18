import discord
from discord.ext import commands
import asyncio
from typing import List

async def wait_for_reaction(bot: commands.Bot, *, ctx: commands.Context, msg: discord.Message, emojis: list, timeout: int):
    def check(reaction, user):
        return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emojis
    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=timeout)
    except asyncio.TimeoutError:
        return
    else:
        return reaction, user

async def wait_for_message(bot: commands.Bot, *, ctx: commands.Context, timeout: int):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content
    try:
        message = await bot.wait_for('message', check=check, timeout=timeout)
    except asyncio.TimeoutError:
        return
    else:
        return message

async def wait_for_first(*tasks: asyncio.Task):
    """
    태스크가 하나라도 완료될 때 까지 기다리고, 그 경우 다른 태스크를 모두 취소한 후 먼저 완료된 태스크 그 자신과 결과를 리턴합니다.
    """
    while True:
        for task in tasks:
            if task.done():
                ts = list(tasks)
                ts.remove(task)
                for x in ts:
                    x.cancel()
                return task
        await asyncio.sleep(0.1)