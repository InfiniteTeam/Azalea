import discord
from discord.ext import commands

class Msglog:
    def __init__(self, logger):
        self.logger = logger

    def log(self, ctx, sent, *args, **kwargs):
        chtypes = {discord.ChannelType.group: 'Group', discord.ChannelType.private: 'DM', discord.ChannelType.text: 'Text', discord.ChannelType.voice: 'Voice'}
        chtypestr = '[Type:] ' + chtypes[ctx.channel.type]
        guildidstr = '[GuildID:] None'
        if ctx.guild:
            guildidstr = '[GuildID:] ' + str(ctx.guild.id)
        channelidstr = '[ChID:] ' + str(ctx.channel.id)
        authoridstr = '[UserID:] ' + str(ctx.author.id)
        msg = '[Msg:] ' + str(ctx.message.content)
        sent = '[Sent:] ' + sent
        logstr = ', '.join([chtypestr, guildidstr, channelidstr, authoridstr, msg, sent])
        self.logger.info(logstr)

    def print(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)