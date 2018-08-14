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

# region -----IMPORTS
import asyncio
import sys

import logging
from datetime import datetime as dt

import aiohttp
import discord
from discord.ext import commands

from pyson import Pyson

# endregion

# region -----LOGS
def commandinfo(ctx):
    # log when a command it's used
    now = dt.now().strftime('%m/%d %H:%M')
    logging.info(f'{now} COMMAND USED; '
                 f'Guild_id: {ctx.message.guild.id} '
                 f'Author_id: {ctx.message.author.id} '
                 f'Invoke: {ctx.message.content}')

def changedefault(ctx):
    # log when a default has been changed
    now = dt.now().strftime('%m/%d %H:%M')
    logging.info(f'{now} DEFAULT CHANGED; '
                 f'Guild_id: {ctx.message.guild.id} '
                 f'Author_id: {ctx.message.author.id} '
                 f'Invoke: {ctx.message.content}')

def taskcomplete(guild):
    # log when the task finishes for a guild
    now = dt.now().strftime('%m/%d %H:%M')
    logging.info(f'{now} Task completed successfully for {guild}')

def catchlog(exception):
    # General log for exceptions
    now = dt.now().strftime('%m/%d %H:%M')
    logging.info(f'{now} EXCEPTION CAUGHT: {exception}')

# TODO: server add/remove log
# endregion

#region -----CHECKS
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
# endregion

# region -----TASKS

async def my_background_task(guild):
    """
    This task creates a seperate loop for each guild it's connected to.
    :param guild:
    :return:
    """
    while not bot.is_closed() and str(guild.id) in jfile.data.keys():
        gid = str(guild.id)
        delay = jfile.data[gid]['delay']
        try:
            await getposts(guild, delay)
            taskcomplete(guild.id)
            await asyncio.sleep(delay)
        except Exception:
            task = asyncio.Task.current_task()
            task.cancel()
            restart_task(guild)
# endregion

# region -----OTHER-FUNCTIONS
async def getposts(guild, delay):
    """
    This function retrieves posts and then sends them to where they need to go per discord guild
    Usage: my_background_task - called in a loop
    :param guild:
    :param delay:
    :return:
    """
    now = dt.utcnow()
    gid = str(guild.id)
    # get default posting channel from json file
    default_channel = guild.get_channel(jfile.data[gid]['default_channel'])

    # get default nsfw channel
    nsfw_channel = guild.get_channel(jfile.data[gid]['NSFW_channel'])

    # reddits that the guild is watching
    reddits = list(jfile.data[gid]['watching'])

    # store nsfw filter
    nsfwfilter = jfile.data[gid]['NSFW_filter']

    # store channel creation option
    create = jfile.data[gid]['create_channel']

    # Don't do anything if the bot can't find reddits or a destination.
    if default_channel is None:
        return

    if reddits is None:
        await default_channel.send('I don\'t have any reddits to watch! Type `r/sub <subreddit>` '
                                   'to start getting posts!')
        return

    for reddit in reddits:
        url = f"https://www.reddit.com/r/{reddit}/new/.json"
        posts = await respcheck(url)

        # If no posts found, skip to next reddit.
        if not posts:
            continue

        images, nsfwimages, nsfw = await appendimages(posts, now, delay, nsfwfilter, nsfw_channel)

        # This skips to next reddit if no posts are new enough.
        if not images and not nsfwimages:
            await asyncio.sleep(1)
            continue

        if create == 0:
            # send to default channels respectively
            if images:
                if nsfw is True:
                    default_channel.edit(nsfw = True)

                for image in images:
                    await default_channel.send(f'From r/{reddit} {image}')
                    await asyncio.sleep(1.5)  # try to prevent the ratelimit from being reached.
            if nsfwimages:
                for image in nsfwimages:
                    await nsfw_channel.send(f'From r/{reddit} {image}')
                    await asyncio.sleep(1.5)
        elif create == 1 and images:
            # send to channels labled for reddits
            sendto = await createchannel(reddit, guild, nsfw)
            await sendto.send('\n'.join(images))

async def respcheck(url):
    """
    This function is used to open up the json file from reddit and get the posts.
    It's used in:
    getposts() - Task
        will continue if no posts are found within guild delay
    sub - command
        will tell user if a connection has been made, or if a subreddit exists.
    :param url:
    :return:
    """
    posts = []
    try:
        # Try to open connection to reddit with async
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:  # 200 == good
                    json = await resp.json()
                    posts = json['data']['children']
                    # puts each post into a dict that can be manipulated
                    posts = list(map(lambda p: p['data'], posts))
                    # Alternate way
                    # posts = list(type('data',(),p['data'])for p in posts)
                    # Allows print(data.author

    except Exception:
        catchlog("Can't get to reddit. Probably 503 error.")

    return posts

async def offjoin(guilds):
    """
    This is for if the bot is offline and joins a guild.
    :param guilds:
    :return:
    """
    for guild in guilds:
        if not str(guild.id) in jfile.data.keys():
            jfile.data.update({
                str(guild.id): {
                    'default_channel': guild.owner.id,
                    'NSFW_channel': 0,
                    'id': guild.id,
                    'delay': 300,
                    'NSFW_filter': 1,
                    'create_channel': 0,
                    'watching': []
                }
            }
            )

            jfile.save

            await guild.owner.send('Thanks for adding me to the guild! There are a few things I need '
                                   'from you or your admins to get running though.\n'
                                   'In the discord guild(NOT HERE),Please set the default channel for '
                                   'me to post in, or turn on the option for me to create a channel '
                                   'for each subreddit. `r/default channel general` or '
                                   '`r/default create`\n'
                                   'Right now I have the default channel set to PM you, so ***I would '
                                   'suggest changing this***. After that, you or your admins '
                                   'can run `r/sub funny` and let the posts flow in!')

async def offremove(guilds):
    """
    This is for if the bot gets kicked while offline
    :param guilds:
    :return:
    """
    guildlist = []
    removed = []
    for guild in guilds:
        guildlist.append(str(guild.id))

    for key in jfile.data:
        if not key in guildlist:
            removed.append(key)

    if removed:
        for guild in removed:
            jfile.data.pop(guild, None)
        jfile.save

async def appendimages(posts, now, delay, nsfwfilter, nsfw_channel):
    """
    Get and return posts.
    :param posts:
    :param now:
    :param delay:
    :param nsfwfilter:
    :param nsfw_channel:
    :return:
    """
    images = []
    nsfwimages = []
    nsfw = False
    for x in posts:
        posttime = dt.utcfromtimestamp(x['created_utc'])
        # if {delay} can't go into total seconds difference once, it gets added to the list of urls
        if (((now - posttime).total_seconds()) / delay) <= 1:
            if nsfwfilter == 1:
                if x['over_18'] is True:
                    continue
                else:
                    images.append(x['url'])
            elif nsfwfilter == 0:
                if nsfw_channel is not None and x['over_18'] is True:
                    nsfwimages.append(x['url'])
                    continue
                images.append(x['url'])

    for x in posts:
        if x['over_18'] is True:
            nsfw = True
            break
    return (images, nsfwimages, nsfw)

async def createchannel(reddit, guild, nsfw):
    """
    Function for creating a channel for each subbed reddit
    :param reddit:
    :param guild:
    :return:
    """
    sendto = discord.utils.get(bot.get_all_channels(), name=reddit.lower(), guild__id=guild.id)

    if sendto is None:
        await guild.create_text_channel(name=reddit.lower())
        await asyncio.sleep(5)  # sleep so that the bot has a chance to see the channel
        sendto = discord.utils.get(bot.get_all_channels(), name=reddit.lower(), guild__id=guild.id)
    if nsfw:
        await sendto.edit(nsfw = True)
    return sendto

async def restart_task(guild):
    asyncio.ensure_future(my_background_task(guild))
# endregion

# region -----BOT CONTENT
bot = commands.Bot(command_prefix = 'rd/', case_insensitive = True, owner_id = 179050708908113920)
# Check to prevent user from trying to use commands in a PM
bot.add_check(nopms)

def start_tasks():
    for guild in bot.guilds:
        asyncio.ensure_future(my_background_task(guild))

    return

start_tasks()

# region -----EVENTS
@bot.event
async def on_ready():
    game = discord.Game("Type rd/help for help")
    await bot.change_presence(activity = game)
    await offjoin(bot.guilds)
    await offremove(bot.guilds)

@bot.event
async def on_guild_join(guild):
    """
    When the bot joins a guild, it will set defaults in the json file and pull all info it needs.
    defaults:
        default channel == 'guild owner'
        nsfw channel == 0
        id == guild id
        delay == 300 (5 minutes)
        nsfw filter == 1
        create channel == 0
        watching == []
    :param guild:
    :return:
    """

    jfile.data.update({
            guild.id: {
                'default_channel': guild.owner.id,
                'NSFW_channel': 0,
                'id': guild.id,
                'delay': 300,
                'NSFW_filter': 1,
                'create_channel': 0,
                'watching': []
            }
        }
    )

    jfile.save

    # message owner about bot usage.
    await guild.owner.send('Thanks for adding me to the guild! There are a few things I need '
                           'from you or your admins to get running though.\n'
                           'In the discord guild(NOT HERE),Please set the default channel for me to '
                           'post in, or turn on the option for me to create a channel for each '
                           'subreddit. `r/default channel general` or `r/default create`\n'
                           'Right now I have the default channel set to PM you, so *I would '
                           'suggest changing this*. After that, you or your admins '
                           'can run `r/sub funny` and let the posts flow in!')

    # create new task for the guild
    asyncio.ensure_future(my_background_task(guild.id))

@bot.event
async def on_guild_remove(guild):
    """
    When a bot leaves/gets kicked, remove the guild from the .json file.
    :param guild:
    :return:
    """
    jfile.data.pop(guild.id, None)
    jfile.save

@bot.event
async def on_command_error(ctx, error):
    # when error is raised, this is what happens.
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.message.delete()
        await ctx.send('Stop it, You can\'t use me in a PM. Go into a guild.')
        catchlog(error)

    if isinstance(error, commands.CommandInvokeError):
        await ctx.message.delete()
        await ctx.send('You messed up the command. Make sure you are doing it right, '
                       'and you are in a discord guild I\'m on.')
        catchlog(error)

    if isinstance(error, commands.CommandNotFound):
        await ctx.message.delete()
        await ctx.send('That\'s not a command.')
        catchlog(error)

    if isinstance(error, commands.BadArgument):
        await ctx.message.delete()
        await ctx.send('Sorry. You provided an argument that doesn\'t quite work.')
        catchlog(error)
# endregion

# region -----COMMANDS

# region -----DEFAULT COMMAND GROUP
@bot.group(name = 'default', case_insensitive = True)
@admin_check()
async def setDefaults(ctx):
    """
    Base command to set the options for a guild.
    Usage: rd/default
    Permissions required: Administrator
    :param ctx:
    :return:
    """
    if ctx.invoked_subcommand is None:
        commandinfo(ctx)
        ctx.message.content = ctx.prefix + 'help ' + ctx.invoked_with
        await bot.process_commands(ctx.message)

@setDefaults.command(name = 'channel')
@admin_check()
async def defaultChannel(ctx, channel: discord.TextChannel=None):
    """
    Set the Default channel for the bot to post in.
    Usage: rd/default channel <channel>
    Permissions required: Administrator
    :param ctx:
    :param channel:
    :return:
    """
    sid = channel.guild.id
    sid = str(sid)
    jfile.data[sid]['default_channel'] = channel.id
    await ctx.send(f"Default channel changed to {channel.mention}\n"
                  f"You will notice this change when I scour reddit again.")
    jfile.save

    changedefault(ctx)

@setDefaults.command(name = 'nsfwchannel')
@admin_check()
async def defaultChannel(ctx, channel: discord.TextChannel=None):
    """
    Set the Default nsfwchannel for the bot to post in.
    Usage: rd/default nsfwchannel <channel>
    Permissions required: Administrator
    :param ctx:
    :param channel:
    :return:
    """

    if channel.is_nsfw() is False:
        await channel.edit(nsfw = True)

    sid = str(channel.guild.id)
    jfile.data[sid]['nsfw_channel'] = channel.id
    await ctx.send(f"Default nsfwchannel changed to {channel.mention}\n"
                   f"You will notice this change when I scour reddit again.")
    jfile.save

    changedefault(ctx)

@setDefaults.command(name = 'delay')
@admin_check()
async def defaulttime(ctx, time):
    """
    This command sets the delay of when the bot should post. It will only get 25 posts max, but some reddits are slow
    TIMES MUST BE: 5m/10m/15m/30m/45m/1h
    I have an upper limit of an hour because if it gets more than 25 posts, that would take a very long time.
    Usage: rd/default delay 10m
    Permissions required: Administrator
    :param ctx:
    :param time:
    :return:
    """
    sid = ctx.message.guild.id
    sid = str(sid)
    if time == '5m':
        jfile.data[sid]['delay'] = 300
        await ctx.send(f'The delay has changed to {time}.')
    elif time == '10m':
        jfile.data[sid]['delay'] = 600
        await ctx.send(f'The delay has changed to {time}.')
    elif time == '15m':
        jfile.data[sid]['delay'] = 900
        await ctx.send(f'The delay has changed to {time}.')
    elif time == '30m':
        jfile.data[sid]['delay'] = 1800
        await ctx.send(f'The delay has changed to {time}.')
    elif time == '45m':
        jfile.data[sid]['delay'] = 2700
        await ctx.send(f'The delay has changed to {time}.')
    elif time == '1h':
        jfile.data[sid]['delay'] = 3600
        await ctx.send(f'The delay has changed to {time}.')
    else:
        await ctx.send('Sorry time must be 5m/10m/15m/30m/45m/1h')

    jfile.save
    changedefault(ctx)

@setDefaults.command(name = 'nsfw')
@admin_check()
async def nsfwFilter(ctx):
    '''
    Toggles the NSFW filter. DEFAULT: ON
    Usage: rd/default nsfw
    Permissions required: Administrator
    :param ctx:
    :return:
    '''
    sid = ctx.message.guild.id
    sid = str(sid)
    if jfile.data[sid]['NSFW_filter'] == 1:
        jfile.data[sid]['NSFW_filter'] = 0
        await ctx.send("NSFW filter has been TURNED OFF. Enjoy your sinful images, loser. Also be sure"
                       "to label your default channel or the NSFW reddit channels as NSFW channels.")
    else:
        jfile.data[sid]['NSFW_filter'] = 1
        await ctx.send("NSFW filter has been TURNED ON. I really don't like looking for those "
                       "images.")
    jfile.save

    changedefault(ctx)

@setDefaults.command(name = 'create')
@admin_check()
async def createChannels(ctx):
    '''
    Toggles the create channels option. DEFAULT: OFF
    Usage: rd/default create
    Permissions required: Administrator
    :param ctx:
    :return:
    '''
    sid = ctx.message.guild.id
    sid = str(sid)
    if jfile.data[sid]['create_channel'] == 1:
        jfile.data[sid]['create_channel'] = 0
        await ctx.send("Creating channels has been TURNED OFF. I will now make all of my posts in "
                       "your default channel.")
    else:
        jfile.data[sid]['create_channel'] = 1
        await ctx.send("Creating channels has been TURNED ON. I can now create channels for each reddit "
                       "that you are watching.")
    jfile.save

    changedefault(ctx)

@setDefaults.command(name = 'show')
async def showDefaults(ctx):
    '''
    This command will show all defaults for the guild.
    Usage: rd/default show
    :param ctx:
    :return:
    '''
    sid = ctx.message.guild.id
    sid = str(sid)
    if sid in jfile.data.keys():
        channel = bot.get_channel(jfile.data[sid]['default_channel'])
        nsfwchannel = bot.get_channel(jfile.data[sid]['NSFW_channel'])

        if not nsfwchannel:
            nsfwchannel = 'Nowhere'

        delay = jfile.data[sid]['delay']

        if jfile.data[sid]['NSFW_filter'] == 0:
            nsfw = 'OFF'
        else:
            nsfw = 'ON'

        if jfile.data[sid]['create_channel'] == 0:
            create = 'OFF'
        else:
            create = 'ON'

        await ctx.send(f"Default channel: {channel}\n"
                       f"Default NSFW channel: {nsfwchannel}\n"
                       f"Delay between posting: {delay} Seconds\n"
                       f"NSFW filter: {nsfw}\n"
                       f"Create channels: {create}")

    changedefault(ctx)

@setDefaults.command(name = 'all')
@admin_check()
async def defaultall(ctx):
    """
    This command sets all options to their default.
    Usage: rd/default all
    Permissions required: Administrator
    :param ctx:
    :return:
    """
    sid = ctx.message.guild.id
    sid = str(sid)
    jfile.data[sid]['default_channel'] = ctx.message.guild.owner.id
    jfile.data[sid]['NSFW_channel'] = 0
    jfile.data[sid]['delay'] = 300
    jfile.data[sid]['NSFW_filter'] = 1
    jfile.data[sid]['create_channel'] = 0
    jfile.data[sid]['watching'] = []
    jfile.save
    await ctx.send('All options have been set to their default. Default channel is the guild owner, so please use'
                   '`r/default channel <channel name>` EX.`r/default channel general`')

# endregion

# region -----ABOUT COMMAND GROUP
@bot.group(name = 'about', case_insensitive = True)
async def about(ctx):
    """
    Base command for all about commands.
    :param ctx:
    :return:
    """
    if ctx.invoked_subcommand is None:
        commandinfo(ctx)
        ctx.message.content = ctx.prefix + 'help ' + ctx.invoked_with
        await bot.process_commands(ctx.message)

@about.command(name = 'bot')
async def botabout(ctx):
    """
    About the bot.
    Usage rd/about bot
    :param ctx:
    :return:
    """
    await ctx.send('```'
                   'This is a bot developed by LittlemanSMG in python using discord.py v1.0.0(rewrite\n'
                   'I use a standard json file to store ID\'s and all the options for each guild.\n'
                   'Code is free to use/look at, following the MIT lisence at '
                   'www.github.com/littlemansmg/pydumpster \n'
                   'Have any recommendations for/issues with the bot? Open up an Issue on github!\n'
                   '```')
    commandinfo(ctx)

@about.command(name = 'dev')
async def devabout(ctx):
    """
    About the Developer
    Usage: rd/about dev
    :param ctx:
    :return:
    """
    await ctx.send('```'
                   "I really don't feel like I need this, but here it is. I'm Scott 'LittlemanSMG' Goes, and"
                   "I made this bot, with some help from the r/discord_bots discord. Originally, this bot was "
                   "made using Praw, a reddit api wrapper, but ran into some massive blocking issues. There was so many"
                   "issues that I had to remake the bot using aiohttp and it's a much better bot now. "
                   "mee6 has this kind of functionality, but I didn't want to deal with all of mee6. I just wanted "
                   "the reddit portion. The original intention was to streamline my meme consumption, but "
                   "I realised that this bot could be used for more than just memes. All of my work is currently "
                   "on github(www.github.com/littlemansmg). It isn't much because i'm still learning, "
                   "but I am getting better.\n"
                   "```")
    commandinfo(ctx)
# endregion

# region -----OTHER COMMANDS

@bot.command(name = 'sub')
@admin_check()
async def subscribe(ctx, *subreddit):
    """
    This command will 'subscribe' to a reddit and will make posts from it.
    Usage: rd/sub <subreddit>
    Ex. rd/sub news funny husky
    Permissions required: Administrator
    :param ctx:
    :param subreddit:
    :return:
    """
    sid = ctx.message.guild.id
    sid = str(sid)
    subs = jfile.data[sid]['watching']
    added = []
    for reddit in subreddit:
        url = f"https://www.reddit.com/r/{reddit}/new/.json"
        posts = await respcheck(url)

        if posts:
            if reddit.lower() in subs:
                await ctx.send(f'{reddit} is already in your list!')
                continue
            else:
                subs.append(reddit.lower())
                added.append(reddit.lower())
        else:
            await ctx.send(f'Sorry, I can\'t reach {reddit}. '
                           f'Check your spelling or make sure that the reddit actually exists.')
    if added:
        jfile.data[sid]['watching'] = subs
        await ctx.send(f"Subreddit(s): {', '.join(added)} added!\n"
                       f"You will notice this change when I scour reddit again.")

        jfile.save

    commandinfo(ctx)

@bot.command(name = 'unsub')
@admin_check()
async def unsub(ctx, *subreddit):
    """
    This command will 'unsubscribe' from a reddit and will no longer make posts.
    Usage: rd/unsub <subreddit>
    Ex. rd/unsub news funny husky
    Permissions required: Administrator
    :param ctx:
    :param subreddit:
    :return:
    """
    sid = ctx.message.guild.id
    sid = str(sid)
    subs = jfile.data[sid]['watching']
    removed = []
    for reddit in subreddit:
        if reddit in subs:
            subs.remove(reddit.lower())
            removed.append(reddit.lower())
        else:
            await ctx.send(f'Subreddit: {reddit} not found. Please make sure you are spelling'
                           f' it correctly.')
    if removed:
        jfile.data[sid]['watching'] = subs
        await ctx.send(f"Subreddit(s): {', '.join(removed)} removed!\n"
                       f"You will notice this change when I scour reddit again.")
        jfile.save

    commandinfo(ctx)

@bot.command(name = 'removeall')
async def removeall(ctx):
    """
    This command will "unsubscribe" from all reddits.
    Usage: rd/removeall
    Permissions required: Administrator
    :param ctx:
    :return:
    """
    sid = ctx.message.guild.id
    sid = str(sid)
    jfile.data[sid]['watching'] = []
    jfile.save
    await ctx.send('You are no longer subbed to any subreddits! Please don\'t get rid of me. :[')

@bot.command(name = 'listsubs')
async def listsubs(ctx):
    """
    Shows a list of subreddits that the bot is subscribed to on a guild.
    Usage rd/listsubs
    :param ctx:
    :return:
    """
    sid = ctx.message.guild.id
    sid = str(sid)
    subs = jfile.data[sid]['watching']
    strsub = ''
    if not subs:
        await ctx.send('This guild isn\'t subbed to anything. Have an adminstrator type '
                       '`r/sub <subreddit name>` to sub. EX `r/sub funny`')
    else:
        for sub in subs:
            strsub += f'r/{sub}\n'

        await ctx.send(f"This guild is subbed to:\n{strsub}")

    commandinfo(ctx)

@bot.command(name = 'fuck', hidden = True, diabled = True)
@admin_check()
async def turnoff(ctx):
    await bot.close()
# endregion

# endregion

# endregion

# region -----STARTUP
if __name__ == '__main__':
    # get token
    token = sys.argv[1]

    # Start Logging
    logging.basicConfig(handlers=[logging.FileHandler('discord.log', 'a', 'utf-8')],
                        level=logging.INFO)

    try:
        jfile = Pyson('options.json')
    except Exception as e:
        catchlog(e)

    # run bot/start loop
    try:
        bot.run(token)
    except Exception as e:
        catchlog(e)
# endregion
