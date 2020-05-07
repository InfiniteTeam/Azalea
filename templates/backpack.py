import discord

class BackPack:
    @staticmethod
    def backpack_embed(ctx, items: list):
        embed = discord.Embed(title=f'💼 `{ctx.author.name}`님의 가방')
        for one in items:
            name = one['icon']['default'] + one['name']
