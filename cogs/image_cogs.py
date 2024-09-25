import re
import asyncio
from bs4 import BeautifulSoup
import urllib.request
import requests
import discord
from discord.ext import commands

class Image_Cogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lastImg = {}

    @commands.command(name='image', help='she will send an image for you.')
    async def image(self, ctx, *content):
        query = '+'.join(content)
        await self.imagehandler(ctx, query)
        
    async def imagehandler(self, ctx, query):
        url = f"https://www.google.com/search?q={query}&tbm=isch"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        res = requests.get(url, headers=headers)
        html_content = res.text

        soup = BeautifulSoup(html_content, 'html.parser')

        images = soup.find_all('img')
        img_links = [image['src'] for image in images]

        if len(img_links) == 0:
            await ctx.send("No images found.")
            return
        #! Note: The first image is a google logo, so we skip it.
        #! Need to find a better way to get the first image.
        await ctx.send(img_links[1])
                

    @commands.command(name="getimg", help="gets an image from discord.")
    async def getimg(self, ctx, message_link: str = None):
        if not message_link:
            async for message in ctx.channel.history(limit=250):
                content = None
                if message.attachments:
                    content = message.attachments
                elif message.embeds:
                    content = message.embeds
                elif message.content:
                    content = re.findall(r"(https?://\S+)", message.content)
                if content:
                    for item in content:
                        if item.url.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                            self.lastImg[ctx.guild.id] = item.url
                            await ctx.send(item.url)
                            return
            await ctx.send("No image found (Read Limit Reachced).")
        elif not message_link.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            await ctx.send("Please provide a valid message link.")
        else:
            self.lastImg[ctx.guild.id] = message_link
            await ctx.send(message_link)

async def setup(bot):
    await bot.add_cog(Image_Cogs(bot))