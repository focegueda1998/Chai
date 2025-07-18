import discord
import asyncio
import urllib
import re
import yt_dlp as youtube_dl
from pytube import Playlist
from discord.ext import commands

def in_voice():
    async def decorator(ctx):
        if ctx.author.voice is None:
            raise commands.CheckFailure("You must be in a voice channel to use this command.")
        return True
    return commands.check(decorator)

class Voice_Cogs(commands.Cog):
    def __init__(self, bot, ydl_opts):
        self.bot = bot
        self.ydl_opts = ydl_opts
        self.queued = {}
        self.loop = {}
        self.tasker = None
        self.ydl = youtube_dl.YoutubeDL(self.ydl_opts)

    @commands.command(name='play', help='she will sing a song for you.')
    @in_voice()
    async def play(self, ctx, *content):
        if not content or len(content) == 0 or (len(content) == 1 and content[0] == ""):
            await ctx.send("a search query or direct youtube link is required.")
            return
        query = '+'.join(content)
        channel = ctx.message.author.voice.channel
        voice = discord.utils.get(ctx.guild.voice_channels, name=channel.name)
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client == None:
            voice_client = await voice.connect()
        else:
            await voice_client.move_to(channel)
        await self.playhandler(ctx, query, voice_client)


    async def playhandler(self, ctx, query, voice_client):
        guild_id = ctx.guild.id
        playlist = re.findall(r"playlist\?list=(\S{34})", query)
        if(len(playlist) > 0):
            await self.playlistHandler(ctx, playlist[0], voice_client)
            return
        res = re.finditer(r"watch\?v=(\S{11})", query)
        vid = next(res, None)
        if not vid:
            res = re.finditer(r"youtu.be/(\S{11})", query)
            vid = next(res, None)
        info = None
        if not vid:
            vid = await self.search(ctx, query)
            if not vid:
                return
        else:
            vid = vid.group(1)
        info = self.ydl.extract_info("https://www.youtube.com/watch?v=" + vid, download=False)
        await ctx.send(f"Added {info['title']} to the queue.")
        try:
            self.queued[guild_id].append(info)
        except:
            self.queued[guild_id] = [info]
            self.loop[guild_id] = False
            await self.player(ctx, voice_client)

    async def playlistHandler(self, ctx, query, voice_client):
        purl = "https://www.youtube.com/playlist?list=" + query
        guild_id = ctx.guild.id
        playlist_content = Playlist(purl)
        try:
            self.queued[guild_id].extend(playlist_content.video_urls)
            await ctx.send(f"Added {len(playlist_content.video_urls)} items to the queue.")
        except:
            self.queued[guild_id] = []
            self.queued[guild_id].extend(playlist_content.video_urls)
            self.loop[guild_id] = False
            await ctx.send(f"Playing {len(playlist_content.video_urls)} items.")
            await self.player(ctx, voice_client)

    #! This is ugly and repeats entires for some reason
    #! TODO: Write a better search function.
    async def search(self, ctx, query):
        msg = await ctx.send("THIS SHIT IS BROKEN, PLEASE USE A LINK INSTEAD.")
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + query)
        res_iter = re.finditer(r"watch\?v=(\S{11})", html.read().decode())
        while(True):
            mcontent = ""
            indexes = [  ]
            while len(indexes) < 5:
                vid = next(res_iter, None)
                if not vid:
                    res_iter = re.finditer(r"watch\?v=(\S{11})", html.read().decode())
                    vid = next(res_iter, None)
                if not vid.group(1) in indexes:
                    indexes.append(vid.group(1))
                    info = self.ydl.extract_info("https://www.youtube.com/watch?v=" + vid.group(1), download=False)
                    mcontent += f"{len(indexes)}. {info['title']} / {info['uploader']} / {info['duration']}s \n"
            await msg.edit(content = mcontent)
            try:
                res = await self.bot.wait_for(
                    "message", 
                    check = lambda x: x.channel.id == ctx.channel.id
                    and x.author.id == ctx.author.id
                    and(
                        x.content == ">"
                        or (int(x.content) > 0 and int(x.content) < 6)
                    ),
                    timeout = 60
                )
            except:
                await msg.edit(content = "Timed out.")
                return None
            if(res.content == ">"):
                await msg.edit(content = "Getting Content...")
            elif(res.content == "exit"):
                await msg.edit(content = "Exiting...")
                return None 
            else :
                print(res.content)
                print(indexes)
                return indexes[int(res.content) - 1]

    async def player(self, ctx, voice_client):
        guild_id = ctx.guild.id
        while len(self.queued[guild_id]) > 0:
            if len(voice_client.channel.members) == 1 and voice_client.is_connected():
                self.queued[guild_id].clear()
                del(self.queued[guild_id])
                del(self.loop[guild_id])
                await voice_client.disconnect()
                return
            song = self.queued[guild_id][0]
            if type(song) == str:
                song = self.ydl.extract_info(song, download=False)
            if int(song['duration']) >= 7500:
                self.queued[guild_id].pop(0)
                await ctx.send(f"{song['title']} is too long.")
            else:
                try:
                    source = discord.FFmpegPCMAudio(
                        song['url'], 
                        #! Should read these options from a config file
                        executable= "/usr/bin/ffmpeg",
                        before_options = "-loglevel debug"
                    )
                    self.tasker = asyncio.create_task(self.coro(ctx, int(song['duration'])))
                    voice_client.play(source)
                    await ctx.send(f"Playing {song['title']}")
                    await self.tasker
                except Exception as e:
                    self.queued[guild_id].pop(0)
                    with open("error.log", "w") as f:
                        f.write(str(e))
                    await ctx.send(f"Uhhhh bot machine broke....")
            if len(self.queued[guild_id]) > 0 and self.loop[guild_id] == False:
                self.queued[guild_id].pop(0)
        self.queued[guild_id].clear()
        del(self.queued[guild_id])
        del(self.loop[guild_id])
        await voice_client.disconnect()
        return

    async def coro(self, ctx, duration):
        await asyncio.sleep(duration + 1)

    @commands.command(name='loop', help='loops the current song.')
    @in_voice()
    async def looper(self, ctx):
        guild_id = ctx.guild.id
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client.is_playing():
            if self.loop[guild_id] == False:
                await ctx.send("Loop = On")
                self.loop[guild_id] = True
            else:
                await ctx.send("Loop = Off")
                self.loop[guild_id] = False
            
    @commands.command(name='skip',help='skips the current song.')
    @in_voice()
    async def skip(self, ctx):
        guild_id = ctx.guild.id
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_client.stop()
        self.tasker.cancel()
        if len(self.queued[guild_id]) > 0: self.queued[guild_id].pop(0)
        await ctx.send("skipped song")
        await self.player(ctx, voice_client)

    @commands.command(name='stop',help='clears the queue and disconnects the bot.')
    @in_voice()
    async def stop(self, ctx):
        guild_id = ctx.guild.id
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_client.stop()
        self.tasker.cancel()
        self.queued[guild_id].clear()
        del(self.queued[guild_id])
        del(self.loop[guild_id])
        await ctx.send("player stopped.")
        await voice_client.disconnect()
    
    @commands.command(name='queue',help='shows the queue.')
    @in_voice()
    async def queue(self, ctx):
        guild_id = ctx.guild.id
        sometext = ""
        i = 0
        if len(self.queued[guild_id]) == 0:
            await ctx.send("Queue is empty.")
            return
        while i < 5 and i < len(self.queued[guild_id]):
            if type(self.queued[guild_id][i]) == str:
                #! Need to create a dict that holds the pre-extracted info.
                self.queued[guild_id][i] = self.ydl.extract_info(self.queued[guild_id][i], download=False)
            sometext += f"{i + 1}. {self.queued[guild_id][i]['title']}\n"
            i += 1
        if i == 5:
            sometext += f"Plus {len(self.queued[guild_id]) - i} items.\n"
        await ctx.send(sometext)

async def setup(bot):
    ydl_opts = {
          'download': False,
          'format': 'bestaudio',
          'cookiefile': 'cookies.txt',
          'extractaudio': True,
          'audioformat': "mp3",
          'restrictfilenames': True,
          'noplaylist': True,
          'nocheckcertificate': True,
          'ignoreerrors': False,
          'logtostderr': False,
          'quiet': True,
          'default_search': 'auto'
        }
    await bot.add_cog(Voice_Cogs(bot, ydl_opts))