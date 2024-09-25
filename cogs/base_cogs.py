import asyncio
import random
import pymongo as pm
from discord.ext import commands

class Base_Cogs(commands.Cog):
    def __init__(self, bot):
        self.barking = {}
        self.barklock = {}
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        message = str(ctx.author.mention) + " "
        print(f"Error: {error}")
        if isinstance(error, commands.errors.CommandNotFound):
            message += "Command not found."
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            message += "Missing arguments."
        elif isinstance(error, commands.errors.CommandInvokeError):
            message += "Something's wrong on my end."
        elif isinstance(error, commands.errors.CheckFailure):
            message += str(error)
        else:
            print(f"Unhandled error: {error}")
            message += "Something went wrong."
        await ctx.send(message)

    @commands.Cog.listener()
    async def on_ready(self):
        client = pm.MongoClient('mongodb://localhost:27017/')
        curDB = client['chai_db']
        print(f'Connected to database {curDB}')

    @commands.command(name='bark', help='she will bark for you.')
    async def bark(self, ctx, *content):
        try:
            self.barking[ctx.guild.id].append(' '.join(content) if len(content) > 0 else "Bark!")
        except:
            self.barking[ctx.guild.id] = [' '.join(content) if len(content) > 0 else "Bark!"]
        if ctx.guild.id not in self.barklock:
            self.barklock[ctx.guild.id] = False
        if self.barklock[ctx.guild.id] == False:
            self.barklock[ctx.guild.id] = True
            while len(self.barking[ctx.guild.id]) > 0:
                msg = self.barking[ctx.guild.id].pop(0)
                barks = random.randint(5, 16)
                for _ in range(barks):
                    await ctx.send(msg)
                    await asyncio.sleep(0.5)
            self.barklock[ctx.guild.id] = False

async def setup(bot):
    await bot.add_cog(Base_Cogs(bot))