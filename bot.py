"""
Pydumpster by Scott "LittlemanSMG" Goes
08/1/2018

Summary:
  This is another remake of Pydump-Async. This version will be the definitive version done in discord-rewrite.py,
  the most up-to-date version of the api.

Description:
  This bot has a few different functions, but it's primarily for Reddit post retrieval and posting to discord.
  It can be used on any guild, it has a few safety precautions like a nsfw filter and admin only commands.

How it works:
  For any reddit url, you can add '.json' to the end of it and get information about every post on that page.
  I use this information to pull the post url and other attributes like nsfw or not.
  To get this to work on multiple guilds, The options get saved into a file called options.json. This file holds
  guild ID's that it's connected to, the options for filters, and the subreddits that they want to pull posts/images
  from.

Other Information:
  Discord.py: https://github.com/Rapptz/discord.py
  Discord.py readthedocs: https://discordpy.readthedocs.io/en/rewrite/index.html
  Github: https://github.com/Littlemansmg/Pydumpster

  Want to learn how to make discord bots in any language?
  Visit r/discord_bots on Reddit, or their Discord guild https://discordapp.com/invite/xRFmHYQ
"""

from discord.ext import commands
import cogs.bot_logs as log
import cogs.resp_functions as respfunc
import cogs.checks as checks
from cogs import bot_commands, events

bot = commands.Bot(command_prefix = 'rd/', case_insensitive = True, owner_id = 179050708908113920)
# Check to prevent user from trying to use commands in a PM
bot.add_check(checks.nopms)

# region -----STARTUP
if __name__ == '__main__':
    # get token
    with open('token.txt') as file:
        token = file.readline()

    # run bot/start loop
    try:
        bot.add_cog(bot_commands.bot_commands(bot))
        bot.add_cog(events.Event(bot))
        bot.add_cog(respfunc.response(bot))
        bot.run(token.strip())
    except Exception as e:
        log.catchlog(e)
# endregion
