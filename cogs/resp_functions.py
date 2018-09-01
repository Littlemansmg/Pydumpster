"""
cog that has commands that rely on respcheck
"""

import discord
from pyson import Pyson
import cogs.bot_logs as log
from datetime import datetime as dt
import asyncio
import aiohttp

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
    # Try to open connection to reddit with async
    try:
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
        log.catchlog(f"Response Failure code {resp.status}")

    return posts

class response:
    def __init__(self, bot):
        self.bot = bot
        self.jfile = Pyson('options.json')
        self.bot.loop.create_task(self.start_tasks(self.bot))

    async def on_guild_join(self, guild):
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
        # TODO: Default sort; bot_commands - various commands + make command
        self.jfile.data.update({
            str(guild.id): {
                'default_channel': guild.owner.id,
                'NSFW_channel': 0,
                'id': guild.id,
                'delay': 300,
                'NSFW_filter': 1,
                'create_channel': 0,
                'watching': []
            }
        })

        self.jfile.save


        # message owner about bot usage.
        await guild.owner.send('Thanks for adding me to the guild! There are a few things I need '
                               'from you or your admins to get running though.\n'
                               'In the discord guild(NOT HERE),Please set the default channel for me to '
                               'post in, or turn on the option for me to create a channel for each '
                               'subreddit. `rd/default channel general` or `rd/default create`\n'
                               'Right now I have the default channel set to PM you, so *I would '
                               'suggest changing this*. After that, you or your admins '
                               'can run `rd/sub funny` and let the posts flow in!')

        # create new task for the guild
        asyncio.ensure_future(self.my_background_task(guild))
        log.guildinfo("Added", guild.id)

    async def my_background_task(self, guild):
        """
        This task creates a seperate loop for each guild it's connected to.
        :param guild:
        :return:
        """
        await self.bot.wait_until_ready()
        while not self.bot.is_closed() and str(guild.id) in self.jfile.data.keys():
            gid = str(guild.id)
            delay = self.jfile.data[gid]['delay']
            try:
                await response.getposts(self, guild, delay)
                log.taskcomplete(guild.id)
                await asyncio.sleep(delay)
            except Exception as e:
                log.catchlog(e)

    async def start_tasks(self, bot):
        await self.bot.wait_until_ready()
        while True:
            if self.bot.is_ready():
                for guild in bot.guilds:
                    asyncio.ensure_future(self.my_background_task(guild))
                    log.catchlog(f'task started for: {guild.id}')
                break

    async def createchannel(self, reddit, guild, nsfw):
        """
        Function for creating a channel for each subbed reddit
        :param reddit:
        :param guild:
        :return:
        """
        sendto = discord.utils.get(self.bot.get_all_channels(), name=reddit.lower(), guild__id=guild.id)

        if sendto is None:
            await guild.create_text_channel(name=reddit.lower())
            await asyncio.sleep(5)  # sleep so that the bot has a chance to see the channel
            sendto = discord.utils.get(self.bot.get_all_channels(), name=reddit.lower(), guild__id=guild.id)
        if nsfw:
            await sendto.edit(nsfw=True)
        return sendto

    async def getposts(self, guild, delay):
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
        default_channel = guild.get_channel(self.jfile.data[gid]['default_channel'])

        # get default nsfw channel
        nsfw_channel = guild.get_channel(self.jfile.data[gid]['NSFW_channel'])

        # reddits that the guild is watching
        reddits = list(self.jfile.data[gid]['watching'])

        # store nsfw filter
        nsfwfilter = self.jfile.data[gid]['NSFW_filter']

        # store channel creation option
        create = self.jfile.data[gid]['create_channel']
        if create == 1:
            nsfw_channel = None

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
                        await default_channel.edit(nsfw=True)

                    for image in images:
                        embed = await embedmaker(image, images)
                        await default_channel.send(embed=embed)
                        await asyncio.sleep(1.5)  # try to prevent the ratelimit from being reached.

                if nsfwimages:
                    for image in nsfwimages:
                        embed = await embedmaker(image, nsfwimages)
                        await nsfw_channel.send(embed=embed)
                        await asyncio.sleep(1.5)

            elif create == 1 and images:
                # send to channels labled for reddits
                sendto = await response.createchannel(self, reddit, guild, nsfw)
                for image in images:
                    embed = await embedmaker(image, images)
                    await sendto.send(embed=embed)

    async def offjoin(self, guilds):
        """
        This is for if the bot is offline and joins a guild.
        :param guilds:
        :return:
        """
        for guild in guilds:
            if not str(guild.id) in self.jfile.data.keys():
                self.jfile.data.update({
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

                self.jfile.save

                await guild.owner.send('Thanks for adding me to the guild! There are a few things I need '
                                       'from you or your admins to get running though.\n'
                                       'In the discord guild(NOT HERE),Please set the default channel for '
                                       'me to post in, or turn on the option for me to create a channel '
                                       'for each subreddit. `rd/default channel general` or '
                                       '`r/default create`\n'
                                       'Right now I have the default channel set to PM you, so ***I would '
                                       'suggest changing this***. After that, you or your admins '
                                       'can run `rd/sub funny` and let the posts flow in!')

    async def offremove(self, guilds):
        """
        This is for if the bot gets kicked while offline
        :param guilds:
        :return:
        """
        guildlist = []
        removed = []
        for guild in guilds:
            guildlist.append(str(guild.id))

        for key in self.jfile.data:
            if not key in guildlist:
                removed.append(key)

        if removed:
            for guild in removed:
                self.jfile.data.pop(guild, None)
            self.jfile.save

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
    # TODO: Set text to embeds, Make gifs work.
    images = {}
    nsfwimages = {}
    nsfw = False
    for x in posts:
        posttime = dt.utcfromtimestamp(x['created_utc'])
        # if {delay} can't go into total seconds difference once, it gets added to the list of urls
        if (((now - posttime).total_seconds()) / delay) <= 1:
            if nsfwfilter == 1:
                if x['over_18'] is True:
                    continue
                else:
                    images.update({
                        x['id']: {
                            'title': x['title'],
                            'author': x['author'],
                            'url': x['url'],
                            'permalink': x['permalink'],
                            'subreddit': x['subreddit']
                        }
                    })
            elif nsfwfilter == 0:
                if nsfw_channel is not None and x['over_18'] is True:
                    nsfwimages.update({
                        x['id']: {
                            'title': x['title'],
                            'author': x['author'],
                            'url': x['url'],
                            'permalink': x['permalink'],
                            'subreddit': x['subreddit']
                        }
                    })
                    continue
                images.update({
                    x['id']: {
                        'title': x['title'],
                        'author': x['author'],
                        'url': x['url'],
                        'permalink': x['permalink'],
                        'subreddit': x['subreddit']
                    }
                })

    for x in posts:
        if x['over_18'] is True:
            nsfw = True
            break
    return (images, nsfwimages, nsfw)

async def embedmaker(id, dictionary):
    embed = discord.Embed(
        title=dictionary[id]['title'],
        url=f"https://www.reddit.com{dictionary[id]['permalink']}",
        color=discord.Color.from_rgb(255, 69, 0)
    )
    embed.set_author(
        name=dictionary[id]['author'],
        url=f"https://www.reddit.com/u/{dictionary[id]['author']}"
    )
    embed.set_image(url=dictionary[id]['url'])
    embed.set_footer(text=f"https://www.reddit.com/r/{dictionary[id]['subreddit']}")
    return embed

