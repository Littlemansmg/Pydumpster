"""
events cog
"""
import discord
from discord.ext import commands
from pyson import Pyson
import cogs.bot_logs as log

class Event():
    def __init__(self, bot):
        jfile = Pyson("options.json")
        self.bot = bot
        self.jfile = jfile

    async def on_ready(self):
        game = discord.Game("Type rd/help for help")
        await self.bot.change_presence(activity=game)

        for guild in self.bot.guilds:
            if str(guild.id) not in self.jfile.data.keys():
                await guild.leave()
                continue

    async def on_guild_remove(self, guild):
        """
        When a bot leaves/gets kicked, remove the guild from the .json file.
        :param guild:
        :return:
        """
        self.jfile.data.pop(str(guild.id), None)
        self.jfile.save

    async def on_command_error(self, ctx, error):
        # when error is raised, this is what happens.
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.message.delete()
            await ctx.send('Stop it, You can\'t use me in a PM. Go into a guild.')
            log.catchlog(error)

        if isinstance(error, commands.CommandInvokeError):
            await ctx.message.delete()
            await ctx.send('You messed up the command. Make sure you are doing it right, '
                           'and you are in a discord guild I\'m on.')
            log.catchlog(error)

        if isinstance(error, commands.CommandNotFound):
            await ctx.message.delete()
            await ctx.send('That\'s not a command.')
            log.catchlog(error)

        if isinstance(error, commands.BadArgument):
            await ctx.message.delete()
            await ctx.send('Sorry. You provided an argument that doesn\'t quite work.')
            log.catchlog(error)
