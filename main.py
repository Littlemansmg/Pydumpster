"""
Pydump-Rewrite by Scott "LittlemanSMG" Goes
07/30/2018

Summary:
  This is another remake of Pydumpster and Pydump-Async. This version will be the definitive version done in
  discord-rewrite.py, the most up-to-date version of the api.

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
  Github: https://github.com/Littlemansmg/Pydump-Rewrite

  Want to learn how to make discord bots in any language?
  Visit r/discord_bots on Reddit, or their Discord guild https://discordapp.com/invite/xRFmHYQ
"""

# region -----IMPORTS
import asyncio

import logging
from datetime import datetime as dt

import aiohttp
import discord
from discord.ext import commands

import fmtjson


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
                 f'guild_id: {ctx.message.guild.id} '
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
# endregion

#region -----CHECKS
def admin_check():
    # check if the user is an admin
    def predicate(ctx):
            return ctx.message.author.guild_permissions.administrator
    return commands.check(predicate)

def nopms(ctx):
    # check for no PM's
    if ctx.message.channel.is_private:
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
    while not bot.is_closed and guild in data.keys():
        delay = data[guild]['delay']
        try:
            await getposts(guild, delay)
            taskcomplete(guild)
            await asyncio.sleep(delay)
        except discord.HTTPException:
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
    # get default posting channel from json file
    destination = bot.get_channel(data[guild]['default_channel'])

    # get default nsfw channel
    nsfw_channel = bot.get_channel(data[guild]['NSFW_channel'])

    # reddits that the guild is watching
    reddits = list(data[guild]['watching'])

    # store nsfw filter
    nsfwfilter = data[guild]['NSFW_filter']

    # store channel creation option
    create = data[guild]['create_channel']

    # Don't do anything if the bot can't find reddits or a destination.
    if destination == None:
        return
    elif reddits == None:
        await bot.send(destination, 'I don\'t have any reddits to watch! Type `r/sub <subreddit>` '
                                            'to start getting posts!')
        return

    for reddit in reddits:
        url = f"https://www.reddit.com/r/{reddit}/new/.json"
        posts = await respcheck(url)

        # If no posts found, skip to next reddit.
        if not posts:
            continue

        images, nsfwimages = await appendimages(posts, now, delay, nsfwfilter, nsfw_channel)

        # This skips to next reddit if no posts are new enough.
        if not images and not nsfwimages:
            await asyncio.sleep(1)
            continue

        if create == 0:
            # send to default channels respectively
            if images:
                for image in images:
                    await bot.send(destination, f'From r/{reddit} {image}')
                    await asyncio.sleep(1.5)  # try to prevent the ratelimit from being reached.
            if nsfwimages:
                for image in nsfwimages:
                    await bot.send(nsfw_channel, f'From r/{reddit} {image}')
                    await asyncio.sleep(1.5)
        elif create == 1 and images:
            # send to channels labled for reddits
            sendto = await createchannel(reddit, data[guild]['id'])
            await bot.send(sendto, '\n'.join(images))

async def respcheck(url):
    """
    This function is used to open up the json file from reddit and get the posts.
    It's used in:
    getposts() - Task
        will continue if no posts are found within 5 minutes
    sub - command
        will tell user if a connection has been made, or if a subreddit exists.
    :param url:
    :return:
    """
    posts = []
    try:
        # Try to open connection to reddit with async
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:  # 200 == good
                    json = await resp.json()
                    posts = json['data']['children']
                    # puts each post into a dict that can be manipulated
                    posts = list(map(lambda p: p['data'], posts))

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
        if not guild.id in data.keys():
            data.update(
                {guild.id: {
                    'default_channel': guild.owner.id,
                    'NSFW_channel': '',
                    'id': guild.id,
                    'watching': [],
                    'NSFW_filter': 1,
                    'create_channel': 0,
                    'delay': 300
                }
                }
            )
            fmtjson.edit_json('options', data)

            await bot.send(guild.owner, 'Thanks for adding me to the guild! There are a few things I need '
                                                 'from you or your admins to get running though.\n'
                                                 'In the discord guild(NOT HERE),Please set the default channel for me to '
                                                 'post in, or turn on the option for me to create a channel for each '
                                                 'subreddit. `r/default channel general` or `r/default create`\n'
                                                 'Right now I have the default channel set to PM you, so *I would '
                                                 'suggest changing this*. After that, you or your admins '
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
        guildlist.append(guild.id)

    for key in data:
        if not key in guildlist:
            removed.append(key)

    if removed:
        for guild in removed:
            data.pop(guild, None)
        fmtjson.edit_json('options', data)

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
    for x in posts:
        posttime = dt.utcfromtimestamp(x['created_utc'])
        # if {delay} can't go into total seconds difference once, it gets added to the list of urls
        if (((now - posttime).total_seconds()) / delay) <= 1:
            if nsfwfilter == 1:
                if x['over_18'] == True:
                    continue
                else:
                    images.append(x['url'])
            elif nsfwfilter == 0:
                if x['over_18'] == True and nsfw_channel:
                    nsfwimages.append(x['url'])
                    continue
                images.append(x['url'])
    return (images, nsfwimages)

async def createchannel(reddit, guild):
    """
    Function for creating a channel for each subbed reddit
    :param reddit:
    :param guild:
    :return:
    """
    sendto = discord.utils.get(bot.get_all_channels(), name=reddit.lower(), guild__id=guild)

    if sendto is None:
        await guild.create_text_channel(
            bot.get_guild(guild), name=reddit.lower(), type=discord.ChannelType.text
        )
        await asyncio.sleep(5)  # sleep so that the bot has a chance to see the channel
        sendto = discord.utils.get(
            bot.get_all_channels(), name=reddit.lower(), guild__id=guild
        )
    return sendto

async def restart_task(sid):
    asyncio.ensure_future(my_background_task(sid))
# endregion

# region -----BOT CONTENT
bot = commands.Bot(command_prefix = 'r/')
# Check to prevent user from trying to use commands in a PM
bot.add_check(nopms)

# region -----EVENTS
@bot.event
async def on_ready():
    await bot.change_presence(game=discord.Game(name='Type r/help for help'))
    await offjoin(bot.guilds)
    await offremove(bot.guilds)
    # create tasks for each guild connected.
    for guild in bot.guilds:
        asyncio.ensure_future(my_background_task(guild.id))

@bot.event
async def on_guild_join(guild):
    """
    When the bot joins a guild, it will set defaults in the json file and pull all info it needs.
    defaults:
        default channel == 'guild owner'
        nsfw channel == ''
        id == guild id
        delay == 300 (5 minutes)
        nsfw filter == 1
        create channel == 0
        watching == []
    :param guild:
    :return:
    """

    data.update(
        {guild.id: {
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
    fmtjson.edit_json('options', data)

    # message owner about bot usage.
    await bot.send(guild.owner, 'Thanks for adding me to the guild! There are a few things I need '
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
    data.pop(guild.id, None)
    fmtjson.edit_json("options", data)

@bot.event
async def on_command_error(error, ctx):
    # when error is raised, this is what happens.
    if isinstance(error, commands.NoPrivateMessage):
        await bot.send(ctx.message.channel, 'Stop it, You can\'t use me in a PM. Go into a guild.')
        catchlog(error)

    if isinstance(error, commands.CommandInvokeError):
        await bot.send(ctx.message.channel, 'You messed up the command. Make sure you are doing it right, '
                                                    'and you are in a discord guild I\'m on.')
        catchlog(error)

    if isinstance(error, commands.CommandNotFound):
        await ctx.message.delete()
        await bot.send(ctx.message.channel, 'Either you didn\'t type a proper command, or you did'
                                                    'but you added a capital letter somewhere. All commands are '
                                                    'lowercase.')
        catchlog(error)
# endregion

# region -----COMMANDS

# region -----DEFAULT COMMAND GROUP
@bot.group(pass_context = True, name = 'default')
@admin_check()
async def setDefaults(ctx):
    """
    Base command to set the options for a guild.
    Usage: r/default
    Permissions required: Administrator
    :param ctx:
    :return:
    """
    if ctx.invoked_subcommand is None:
        commandinfo(ctx)
        ctx.message.content = ctx.prefix + 'help ' + ctx.invoked_with
        await bot.process_commands(ctx.message)

@setDefaults.command(pass_context = True, name = 'channel')
@admin_check()
async def defaultChannel(ctx, channel):
    """
    Set the Default channel for the bot to post in.
    Usage: r/default channel <channel>
    Permissions required: Administrator
    :param ctx:
    :param channel:
    :return:
    """
    newchannel = discord.utils.get(bot.get_all_channels(), name = channel, guild__id = ctx.message.guild.id)

    if not newchannel:
        raise commands.CommandInvokeError

    sid = ctx.message.guild.id
    data[sid]['default_channel'] = newchannel.id
    await bot.say(f"Default channel changed to {newchannel.mention}\n"
                  f"You will notice this change when I scour reddit again.")
    fmtjson.edit_json('options', data)

    changedefault(ctx)

@setDefaults.command(pass_context = True, name = 'nsfwchannel')
@admin_check()
async def defaultChannel(ctx, channel):
    """
    Set the Default nsfwchannel for the bot to post in.
    Usage: r/default nsfwchannel <channel>
    Permissions required: Administrator
    :param ctx:
    :param channel:
    :return:
    """
    newchannel = discord.utils.get(bot.get_all_channels(), name = channel, guild__id = ctx.message.guild.id)

    if not newchannel:
        raise commands.CommandInvokeError

    sid = ctx.message.guild.id
    data[sid]['NSFW_channel'] = newchannel.id
    await bot.say(f"NSFW default channel changed to {newchannel.mention}\n"
                  f"You will notice this change when I scour reddit again.")
    fmtjson.edit_json('options', data)

    changedefault(ctx)

@setDefaults.command(pass_context = True, name = 'delay')
@admin_check()
async def defaulttime(ctx, time):
    """
    This command sets the delay of when the bot should post. It will only get 25 posts max, but some reddits are slow
    TIMES MUST BE: 5m/10m/15m/30m/45m/1h
    I have an upper limit of an hour because if it gets more than 25 posts, that would take a very long time.
    Usage: r/default delay 10m
    Permissions required: Administrator
    :param ctx:
    :param time:
    :return:
    """
    sid = ctx.message.guild.id
    if time == '5m':
        data[sid]['delay'] = 300
        await bot.say(f'The delay has changed to {time}.')
    elif time == '10m':
        data[sid]['delay'] = 600
        await bot.say(f'The delay has changed to {time}.')
    elif time == '15m':
        data[sid]['delay'] = 900
        await bot.say(f'The delay has changed to {time}.')
    elif time == '30m':
        data[sid]['delay'] = 1800
        await bot.say(f'The delay has changed to {time}.')
    elif time == '45m':
        data[sid]['delay'] = 2700
        await bot.say(f'The delay has changed to {time}.')
    elif time == '1h':
        data[sid]['delay'] = 3600
        await bot.say(f'The delay has changed to {time}.')
    else:
        await bot.say('Sorry time must be 5m/10m/15m/30m/45m/1h')

    fmtjson.edit_json('options', data)
    changedefault(ctx)

@setDefaults.command(pass_context = True, name = 'nsfw')
@admin_check()
async def nsfwFilter(ctx):
    '''
    Toggles the NSFW filter. DEFAULT: ON
    Usage: r/default nsfw
    Permissions required: Administrator
    :param ctx:
    :return:
    '''
    sid = ctx.message.guild.id
    if data[sid]['NSFW_filter'] == 1:
        data[sid]['NSFW_filter'] = 0
        await bot.say("NSFW filter has been TURNED OFF. Enjoy your sinful images, loser. Also be sure"
                      "to label your default channel or the NSFW reddit channels as NSFW channels.")
    else:
        data[sid]['NSFW_filter'] = 1
        await bot.say("NSFW filter has been TURNED ON. I really don't like looking for those "
                      "images.")
    fmtjson.edit_json('options', data)

    changedefault(ctx)

@setDefaults.command(pass_context = True, name = 'create')
@admin_check()
async def createChannels(ctx):
    '''
    Toggles the create channels option. DEFAULT: OFF
    Usage: r/default create
    Permissions required: Administrator
    :param ctx:
    :return:
    '''
    sid = ctx.message.guild.id
    if data[sid]['create_channel'] == 1:
        data[sid]['create_channel'] = 0
        await bot.say("Creating channels has been TURNED OFF. I will now make all of my posts in "
                      "your default channel.")
    else:
        data[sid]['create_channel'] = 1
        await bot.say("Creating channels has been TURNED ON. I can now create channels for each reddit "
                      "that you are watching.")
    fmtjson.edit_json('options', data)

    changedefault(ctx)

@setDefaults.command(pass_context = True, name = 'show')
async def showDefaults(ctx):
    '''
    This command will show all defaults for the guild.
    Usage: r/default show
    :param ctx:
    :return:
    '''
    sid = ctx.message.guild.id
    if sid in data.keys():
        channel = bot.get_channel(data[sid]['default_channel'])
        nsfwchannel = bot.get_channel(data[sid]['NSFW_channel'])

        if not nsfwchannel:
            nsfwchannel = 'Nowhere'

        delay = data[sid]['delay']

        if data[sid]['NSFW_filter'] == 0:
            nsfw = 'OFF'
        else:
            nsfw = 'ON'

        if data[sid]['create_channel'] == 0:
            create = 'OFF'
        else:
            create = 'ON'

        await bot.say(f"Default channel: {channel}\n"
                      f"Default NSFW channel: {nsfwchannel}\n"
                      f"Delay between posting: {delay} Seconds\n"
                      f"NSFW filter: {nsfw}\n"
                      f"Create channels: {create}")

    changedefault(ctx)

@setDefaults.command(pass_context = True, name = 'all')
@admin_check()
async def defaultall(ctx):
    """
    This command sets all options to their default.
    Usage: r/default all
    Permissions required: Administrator
    :param ctx:
    :return:
    """
    sid = ctx.message.guild.id
    data[sid]['default_channel'] = ctx.message.guild.owner.id
    data[sid]['NSFW_channel'] = ''
    data[sid]['delay'] = 300
    data[sid]['NSFW_filter'] = 1
    data[sid]['create_channel'] = 0
    data[sid]['watching'] = []
    fmtjson.edit_json('options', data)
    await bot.say('All options have been set to their default. Default channel is the guild owner, so please use'
                  '`r/default channel <channel name>` EX.`r/default channel general`')

# endregion

# region -----ABOUT COMMAND GROUP
@bot.group(pass_context = True, name = 'about')
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

@about.command(pass_context = True, name = 'bot')
async def botabout(ctx):
    """
    About the bot.
    Usage r/about bot
    :param ctx:
    :return:
    """
    await bot.say('```'
                  'This is a bot developed by LittlemanSMG in python using discord.py v0.16.12\n'
                  'I use a standard json file to store ID\'s and all the options for each guild.\n'
                  'Code is free to use/look at, following the MIT lisence at '
                  'www.github.com/littlemansmg/pydump-rewrite \n'
                  'Have any recommendations for/issues with the bot? Open up an Issue on github!\n'
                  '```')
    commandinfo(ctx)

@about.command(pass_context = True, name = 'dev')
async def devabout(ctx):
    """
    About the Developer
    Usage: r/about dev
    :param ctx:
    :return:
    """
    await bot.say('```'
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

@bot.command(pass_context = True, name = 'sub')
@admin_check()
async def subscribe(ctx, *subreddit):
    """
    This command will 'subscribe' to a reddit and will make posts from it.
    Usage: r/sub <subreddit>
    Ex. r/sub news funny husky
    Permissions required: Administrator
    :param ctx:
    :param subreddit:
    :return:
    """
    sid = ctx.message.guild.id
    subs = data[sid]['watching']
    added = []
    for reddit in subreddit:
        url = f"https://www.reddit.com/r/{reddit}/new/.json"
        posts = await respcheck(url)

        if posts:
            if reddit.lower() in subs:
                await bot.say(f'{reddit} is already in your list!')
                continue
            else:
                subs.append(reddit.lower())
                added.append(reddit.lower())
        else:
            await bot.say(f'Sorry, I can\'t reach {reddit}. '
                          f'Check your spelling or make sure that the reddit actually exists.')
    if added:
        data[sid]['watching'] = subs
        await bot.say(f"Subreddit(s): {', '.join(added)} added!\n"
                      f"You will notice this change when I scour reddit again.")

        fmtjson.edit_json('options', data)

    commandinfo(ctx)

@bot.command(pass_context = True, name = 'unsub')
@admin_check()
async def unsub(ctx, *subreddit):
    """
    This command will 'unsubscribe' from a reddit and will no longer make posts.
    Usage: r/unsub <subreddit>
    Ex. r/unsub news funny husky
    Permissions required: Administrator
    :param ctx:
    :param subreddit:
    :return:
    """
    sid = ctx.message.guild.id
    subs = data[sid]['watching']
    removed = []
    for reddit in subreddit:
        if reddit in subs:
            subs.remove(reddit.lower())
            removed.append(reddit.lower())
        else:
            await bot.say(f'Subreddit: {reddit} not found. Please make sure you are spelling'
                          f' it correctly.')
    if removed:
        data[sid]['watching'] = subs
        await bot.say(f"Subreddit(s): {', '.join(removed)} removed!\n"
                      f"You will notice this change when I scour reddit again.")
        fmtjson.edit_json('options', data)

    commandinfo(ctx)

@bot.command(pass_context = True, name = 'removeall')
async def removeall(ctx):
    """
    This command will "unsubscribe" from all reddits.
    Usage: r/removeall
    Permissions required: Administrator
    :param ctx:
    :return:
    """
    sid = ctx.message.guild.id
    data[sid]['watching'] = []
    fmtjson.edit_json('options', data)
    await bot.say('You are no longer subbed to any subreddits! Please don\'t get rid of me. :[')

@bot.command(pass_context = True, name = 'listsubs')
async def listsubs(ctx):
    """
    Shows a list of subreddits that the bot is subscribed to on a guild.
    Usage r/listsubs
    :param ctx:
    :return:
    """
    sid = ctx.message.guild.id
    subs = data[sid]['watching']
    strsub = ''
    if not subs:
        await bot.say('This guild isn\'t subbed to anything. Have an adminstrator type '
                      '`r/sub <subreddit name>` to sub. EX `r/sub funny`')
    else:
        for sub in subs:
            strsub += f'r/{sub}\n'

        await bot.say(f"This guild is subbed to:\n{strsub}")

    commandinfo(ctx)

@bot.command(pass_context = True, name = 'fuckmeupfam', hidden = True, disabled = True)
@admin_check()
async def fuckmeupfam(ctx):
    await bot.close()
# endregion

# endregion

# endregion

# region -----STARTUP
if __name__ == '__main__':
    # get token
    with open('token.txt') as token:
        token = token.readline()

    # Start Logging
    logging.basicConfig(handlers=[logging.FileHandler('discord.log', 'a', 'utf-8')],
                        level=logging.INFO)

    try:
        data = fmtjson.read_json('options')
    except Exception as e:
        catchlog(e)

    # run bot/start loop
    try:
        bot.loop.run_until_complete(bot.run(token.strip()))
    except Exception as e:
        catchlog(e)
# endregion
