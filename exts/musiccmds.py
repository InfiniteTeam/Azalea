import discord
from discord.ext import commands
import datetime
import asyncio
import youtube_dl
import uuid
import os
import typing
from utils.basecog import BaseCog

class Musiccmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)

    @commands.group(name='뮤직', aliases=['음악', '노래'], invoke_without_command=True)
    async def _music(self, ctx: commands.Context):
        pass

    @_music.command(name='끊기')
    async def _leave(self, ctx: commands.Context):
        voice = ctx.voice_client
        if voice:
            await voice.disconnect()

    @_music.command(name='재생')
    async def _play(self, ctx: commands.Context, url):
        voice: discord.VoiceClient = ctx.voice_client
        if voice:
            if voice.is_playing():
                voice.stop()
        else:
            channel = ctx.author.voice.channel
            if channel:
                await channel.connect()
                voice: discord.VoiceClient = ctx.voice_client
            else:
                await ctx.send('먼저 음성 채널에 들어가주세요')
                return
        
        await ctx.send('음악을 다운로드하고 있습니다...')
        uid = uuid.uuid4().hex
        opts = {
            'outtmpl': f'./tmp/ytdl_%(title)s-%(id)s-{uid}.%(ext)s',
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        }

        with youtube_dl.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            dl = self.client.loop.run_in_executor(None, ydl.download, [url])
            
            while True:
                for f in os.listdir('./tmp/'):
                    if f.startswith('ytdl') and '-'+uid+'.mp3' in f:
                        name = './tmp/' + f
                        break
                    await asyncio.sleep(0.1)
                else:
                    continue
                break

            print('done')
            embed = discord.Embed(title='현재 재생 중', description='[{}]({})'.format(info.get('title'), url), color=self.color['info'])
            await ctx.send(embed=embed)
            voice.play(discord.FFmpegPCMAudio(name))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.20
            
            while voice.is_playing():
                await asyncio.sleep(0.1)

            try:
                os.remove(name)
            except:
                pass

    @_music.command(name='볼륨')
    async def _volume(self, ctx: commands.Context, v: int):
        ctx.voice_client.source.volume = v/100

    @_music.command(name='정지')
    async def _stop(self, ctx: commands.Context):
        voice: discord.VoiceClient = ctx.voice_client
        if voice and voice.is_playing():
            voice.pause()
            await ctx.send('일시정지 되었습니다')

    @_music.command(name='계속')
    async def _resume(self, ctx: commands.Context):
        voice: discord.VoiceClient = ctx.voice_client
        if voice and voice.is_paused():
            voice.resume()
            await ctx.send('계속 재생합니다')

    @_music.command(name='이동')
    async def _move_to(self, ctx: commands.Context):
        voice: discord.VoiceClient = ctx.voice_client
        if voice:
            channel = ctx.author.voice.channel
            if channel:
                await voice.move_to(channel)
                voice: discord.VoiceClient = ctx.voice_client

def setup(client):
    cog = Musiccmds(client)
    client.add_cog(cog)