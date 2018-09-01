"""
Checks cog for Pydumpster
"""

import discord
from discord.ext import commands

# TODO: Set up role based checks; resp_functions - on guild join; bot_commands - various commands + make commands

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
