import discord
from discord.ext import commands

class Emoji:
    def __init__(self, client: discord.Client, guild: int, emojis: dict):
        self.guild = guild
        self.emojis = emojis
        self.client = client

    def get(self, ctx: commands.Context, name: str):
        if ctx is None or not ctx.guild or ctx.channel.permissions_for(ctx.guild.get_member(self.client.user.id)).external_emojis:
            return self.client.get_emoji(self.emojis[name]['default'])
        else:
            try:
                return self.emojis[name]['replace']
            except KeyError:
                return self.client.get_emoji(self.emojis[name]['default'])

    def getid(self, name):
        return self.emojis[name]