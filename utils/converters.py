from discord.ext import commands
from . import datamgr

class EnchantmentConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg) -> datamgr.EnchantmentData:
        enchant = arg.split('=')
        return datamgr.EnchantmentData(enchant[0], enchant[1])