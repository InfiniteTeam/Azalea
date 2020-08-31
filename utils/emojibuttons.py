import discord
import asyncio
from . import pager, errors

class PageButton:
    emojis = ['⏪','◀', '⏹', '▶', '⏩']
    @classmethod
    async def buttonctrl(cls, reaction: discord.Reaction, user: discord.User, pgr: pager.Pager, *, double: int=5):
        emj = reaction.emoji
        try:
            if emj == '⏪':
                if double == 0:
                    pgr.go_first(exc=True)
                else:
                    pgr.minus(double, exc=True)
            elif emj == '⏩':
                if double == 0:
                    pgr.go_end(exc=True)
                else:
                    pgr.plus(double, exc=True)
            elif emj == '◀':
                pgr.prev(exc=True)
            elif emj == '▶':
                pgr.next(exc=True)
            elif emj == '⏹':
                return reaction.message.clear_reactions()
        except StopIteration:
            await reaction.remove(user)
            return
        else:
            return reaction.remove(user)