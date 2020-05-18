import discord
import asyncio
from exts.utils import pager, errors

class PageButton:
    emojis = ['⏪','◀', '⏹', '▶', '⏩']
    @classmethod
    async def buttonctrl(cls, reaction: discord.Reaction, user: discord.User, pgr: pager.Pager, willdo=None):
        emj = str(reaction.emoji)
        try:
            if emj == '⏪':
                pgr.go_first(exc=True)
            elif emj == '⏩':
                pgr.go_end(exc=True)
            elif emj == '◀':
                pgr.prev(exc=True)
            elif emj == '▶':
                pgr.next(exc=True)
            elif emj == '⏹':
                await reaction.message.clear_reactions()
                return None
        except StopIteration:
            await reaction.message.remove_reaction(emj, user)
            return None
        else:
            return reaction.message.remove_reaction(emj, user)