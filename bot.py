import os
import discord
import asyncio
from discord.ext import commands
from cogs import image_cogs, base_cogs, voice_cogs
from dotenv import load_dotenv

class Chai(commands.Bot):
    def __init__(self, prefix = '$chai ', intents = discord.Intents.all(), cogs_list = []):
        intents.messages = True
        super().__init__(command_prefix = prefix, intents = intents)

        self.cogs_list = cogs_list

    async def setup(self):
        load_dotenv()
        TOKEN = os.getenv('TOKEN')

        for cog in self.cogs_list:
            await self.load_extension(cog)

        await self.start(TOKEN)

if __name__ == '__main__':
    chai = Chai (
        cogs_list = [
            'cogs.image_cogs',
            'cogs.base_cogs', 
            'cogs.voice_cogs'
        ]
    )

    asyncio.run(chai.setup())