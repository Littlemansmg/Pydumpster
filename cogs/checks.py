"""
Checks cog for Pydumpster
"""

import discord
from discord.ext import commands

def admin_check():
    # check if the user is an admin
    def predicate(ctx):
            return ctx.message.author.guild_permissions.administrator
    return commands.check(predicate)

def nopms(ctx):
    # check for no PM's
    if isinstance(ctx.message.channel, discord.abc.PrivateChannel):
        raise commands.NoPrivateMessage
    else:
        return True
