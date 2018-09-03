"""
Command cog for Pydumpster
"""

import discord
from discord.ext import commands

from pyson import Pyson
import cogs.checks as checks
import cogs.bot_logs as log
import cogs.resp_functions as resp

class bot_commands:
    def __init__(self, bot):
        self.bot = bot
        self.jfile = Pyson('options.json')

    # TODO: Make a personal help command to make it easier to use.
    # TODO: Cog loader and unloader?

    # region -----DEFAULT COMMAND GROUP
    @commands.group(name='default', case_insensitive=True)
    @checks.admin_check()
    async def setDefaults(self, ctx):
        """
        Base command to set the options for a guild.
        Usage: rd/default
        Permissions required: Administrator
        :param ctx:
        :return:
        """
        if ctx.invoked_subcommand is None:
            log.commandinfo(ctx)
            ctx.message.content = ctx.prefix + 'help ' + ctx.invoked_with
            await self.bot.process_commands(ctx.message)

    @setDefaults.command(name='channel')
    @checks.admin_check()
    async def defaultChannel(self, ctx, channel: discord.TextChannel = None):
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
        self.jfile.data[sid]['default_channel'] = channel.id
        await ctx.send(f"Default channel changed to {channel.mention}\n"
                       f"You will notice this change when I scour reddit again.")
        self.jfile.save

        log.changedefault(ctx)

    @setDefaults.command(name='nsfwchannel')
    @checks.admin_check()
    async def defaultNSFWChannel(self, ctx, channel: discord.TextChannel = None):
        """
        Set the Default nsfwchannel for the bot to post in.
        Usage: rd/default nsfwchannel <channel>
        Permissions required: Administrator
        :param ctx:
        :param channel:
        :return:
        """

        if channel.is_nsfw() is False:
            await channel.edit(nsfw=True)

        sid = str(channel.guild.id)
        self.jfile.data[sid]['NSFW_channel'] = channel.id
        await ctx.send(f"Default nsfwchannel changed to {channel.mention}\n"
                       f"You will notice this change when I scour reddit again.")
        self.jfile.save

        log.changedefault(ctx)

    @setDefaults.command(name='delay')
    @checks.admin_check()
    async def defaulttime(self, ctx, time):
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
            self.jfile.data[sid]['delay'] = 300
            await ctx.send(f'The delay has changed to {time}.')
        elif time == '10m':
            self.jfile.data[sid]['delay'] = 600
            await ctx.send(f'The delay has changed to {time}.')
        elif time == '15m':
            self.jfile.data[sid]['delay'] = 900
            await ctx.send(f'The delay has changed to {time}.')
        elif time == '30m':
            self.jfile.data[sid]['delay'] = 1800
            await ctx.send(f'The delay has changed to {time}.')
        elif time == '45m':
            self.jfile.data[sid]['delay'] = 2700
            await ctx.send(f'The delay has changed to {time}.')
        elif time == '1h':
            self.jfile.data[sid]['delay'] = 3600
            await ctx.send(f'The delay has changed to {time}.')
        else:
            await ctx.send('Sorry time must be 5m/10m/15m/30m/45m/1h')

        self.jfile.save
        log.changedefault(ctx)

    @setDefaults.command(name='nsfw')
    @checks.admin_check()
    async def nsfwFilter(self, ctx):
        '''
        Toggles the NSFW filter. DEFAULT: ON
        Usage: rd/default nsfw
        Permissions required: Administrator
        :param ctx:
        :return:
        '''
        sid = ctx.message.guild.id
        sid = str(sid)
        if self.jfile.data[sid]['NSFW_filter'] == 1:
            self.jfile.data[sid]['NSFW_filter'] = 0
            await ctx.send("NSFW filter has been TURNED OFF. Enjoy your sinful images, loser. Also be sure"
                           "to label your default channel or the NSFW reddit channels as NSFW channels.")
        else:
            self.jfile.data[sid]['NSFW_filter'] = 1
            await ctx.send("NSFW filter has been TURNED ON. I really don't like looking for those "
                           "images.")
        self.jfile.save

        log.changedefault(ctx)

    @setDefaults.command(name='create')
    @checks.admin_check()
    async def createChannels(self, ctx):
        '''
        Toggles the create channels option. DEFAULT: OFF
        Usage: rd/default create
        Permissions required: Administrator
        :param ctx:
        :return:
        '''
        sid = ctx.message.guild.id
        sid = str(sid)
        if self.jfile.data[sid]['create_channel'] == 1:
            self.jfile.data[sid]['create_channel'] = 0
            await ctx.send("Creating channels has been TURNED OFF. I will now make all of my posts in "
                           "your default channel.")
        else:
            self.jfile.data[sid]['create_channel'] = 1
            await ctx.send("Creating channels has been TURNED ON. I can now create channels for each reddit "
                           "that you are watching.")

        self.jfile.save

        log.changedefault(ctx)

    @setDefaults.command(name='show')
    async def showDefaults(self, ctx):
        '''
        This command will show all defaults for the guild.
        Usage: rd/default show
        :param ctx:
        :return:
        '''
        sid = ctx.message.guild.id
        sid = str(sid)
        if sid in self.jfile.data.keys():
            channel = self.bot.get_channel(self.jfile.data[sid]['default_channel'])
            nsfwchannel = self.bot.get_channel(self.jfile.data[sid]['NSFW_channel'])

            if not nsfwchannel:
                nsfwchannel = 'Nowhere'

            delay = self.jfile.data[sid]['delay']

            if self.jfile.data[sid]['NSFW_filter'] == 0:
                nsfw = 'OFF'
            else:
                nsfw = 'ON'

            if self.jfile.data[sid]['create_channel'] == 0:
                create = 'OFF'
            else:
                create = 'ON'

            await ctx.send(f"Default channel: {channel}\n"
                           f"Default NSFW channel: {nsfwchannel}\n"
                           f"Delay between posting: {delay} Seconds\n"
                           f"NSFW filter: {nsfw}\n"
                           f"Create channels: {create}")

        log.changedefault(ctx)

    @setDefaults.command(name='all')
    @checks.admin_check()
    async def defaultall(self, ctx):
        """
        This command sets all options to their default.
        Usage: rd/default all
        Permissions required: Administrator
        :param ctx:
        :return:
        """
        sid = ctx.message.guild.id
        sid = str(sid)
        self.jfile.data[sid]['default_channel'] = ctx.message.guild.owner.id
        self.jfile.data[sid]['NSFW_channel'] = 0
        self.jfile.data[sid]['delay'] = 300
        self.jfile.data[sid]['NSFW_filter'] = 1
        self.jfile.data[sid]['create_channel'] = 0
        self.jfile.data[sid]['watching'] = []
        self.jfile.save
        await ctx.send('All options have been set to their default. Default channel is the guild owner, so please use'
                       '`r/default channel <channel name>` EX.`r/default channel general`')
    # endregion

    # region -----ABOUT COMMAND GROUP
    @commands.group(name='about', case_insensitive=True)
    async def about(self, ctx):
        """
        Base command for all about commands.
        :param ctx:
        :return:
        """
        if ctx.invoked_subcommand is None:
            log.commandinfo(ctx)
            ctx.message.content = ctx.prefix + 'help ' + ctx.invoked_with
            await self.bot.process_commands(ctx.message)

    @about.command(name='bot')
    async def botabout(self, ctx):
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
        log.commandinfo(ctx)

    @about.command(name='dev')
    async def devabout(self, ctx):
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
        log.commandinfo(ctx)
    # endregion

    # region -----OTHER COMMANDS
    @commands.command(name='sub')
    @checks.admin_check()
    async def subscribe(self, ctx, *subreddit):
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
        subs = self.jfile.data[sid]['watching']
        added = []
        for reddit in subreddit:
            url = f"https://www.reddit.com/r/{reddit}/new/.json"
            posts = await resp.respcheck(url)

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
            self.jfile.data[sid]['watching'] = subs
            await ctx.send(f"Subreddit(s): {', '.join(added)} added!\n"
                           f"You will notice this change when I scour reddit again.")

            self.jfile.save

        log.commandinfo(ctx)

    @commands.command(name='unsub')
    @checks.admin_check()
    async def unsub(self, ctx, *subreddit):
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
        subs = self.jfile.data[sid]['watching']
        removed = []
        for reddit in subreddit:
            if reddit in subs:
                subs.remove(reddit.lower())
                removed.append(reddit.lower())
            else:
                await ctx.send(f'Subreddit: {reddit} not found. Please make sure you are spelling'
                               f' it correctly.')
        if removed:
            self.jfile.data[sid]['watching'] = subs
            await ctx.send(f"Subreddit(s): {', '.join(removed)} removed!\n"
                           f"You will notice this change when I scour reddit again.")
            self.jfile.save

        log.commandinfo(ctx)

    @commands.command(name='removeall')
    async def removeall(self, ctx):
        """
        This command will "unsubscribe" from all reddits.
        Usage: rd/removeall
        Permissions required: Administrator
        :param ctx:
        :return:
        """
        sid = ctx.message.guild.id
        sid = str(sid)
        self.jfile.data[sid]['watching'] = []
        self.jfile.save
        await ctx.send('You are no longer subbed to any subreddits! Please don\'t get rid of me. :[')

    @commands.command(name='listsubs')
    async def listsubs(self, ctx):
        """
        Shows a list of subreddits that the bot is subscribed to on a guild.
        Usage rd/listsubs
        :param ctx:
        :return:
        """
        sid = ctx.message.guild.id
        sid = str(sid)
        subs = self.jfile.data[sid]['watching']
        strsub = ''
        if not subs:
            await ctx.send('This guild isn\'t subbed to anything. Have an adminstrator type '
                           '`r/sub <subreddit name>` to sub. EX `r/sub funny`')
        else:
            for sub in subs:
                strsub += f'r/{sub}\n'

            await ctx.send(f"This guild is subbed to:\n{strsub}")

        log.commandinfo(ctx)

    @commands.command(name='suggest')
    @commands.cooldown(1, 120.0, commands.BucketType.user)
    async def suggest(self, ctx, option, *, suggestion):
        """
        Suggestion command that sends them to the creator.
        This command is on a 2 minute cooldown after one use
        Example: rd/suggest Feature Your bot is dumb, stop programming.
        :param ctx:
        :param option:
        :param suggestion:
        :return:
        """
        await ctx.message.delete()
        features = ['feature', 'bug', 'general']

        embed = discord.Embed(
            title='Suggestion',
            color=discord.Color.from_rgb(0, 128, 0)
        )

        if option.lower() not in features:
            embed.add_field(name='General', value=f'{option} {suggestion}')
        else:
            option = f'{option[0].upper()}{option[1:]}'
            embed.add_field(name=option, value=suggestion)

        owner = self.bot.get_user(self.bot.owner_id)

        await owner.send(embed=embed)
        await ctx.send('Your suggestion has been sent.')
        log.commandinfo(ctx)
    # endregion

    # region -----Owner Commands
    @commands.command(name='fuck', hidden=True)
    @commands.is_owner()
    async def turnoff(self, ctx):
        await self.bot.logout()
        await self.bot.close()

    @commands.command(name='update', hidden=True)
    @commands.is_owner()
    async def update(self, ctx, title, *message: str):
        for guild in self.bot.guilds:
            gid = str(guild.id)
            avatar = self.bot.user.avatar_url
            default_channel = guild.get_channel(self.jfile.data[gid]['default_channel'])
            embed = discord.Embed(
                title='Important message from dev!',
                url='https://www.github.com/littlemansmg/pydumpster',
                color=discord.Color.from_rgb(0, 128, 0)
            )
            embed.set_thumbnail(url=avatar)
            embed.add_field(name=title, value=" ".join(message))
            embed.add_field(name='Github', value="www.github.com/littlemansmg/pydumpster.", inline=False)
            embed.add_field(name = "Up Next", value = ">>Set up role based checks, so instead of "
                                                      "just admins, people with x role can use a command. \n"
                                                      ">>Add a command to change the default sort for reddit. i.e. "
                                                      "new/hot/top. \n"
                                                      ">>(Added, Thanks Runew0lf)Personalize the help command. "
                                                      "It looks really bland, and weird to use, so I'm going to make"
                                                      " it look better.")
            embed.add_field(name = "Known Bugs", value = "(Actually fixed) Titles and Posts that are too long would "
                                                         "cause errors in my logs and repost for an extended period "
                                                         "of time. I have eliminated this issue."
                                                         "issue.")
            embed.set_footer(text="Want to learn how to make bots yourself? Join r/discord_bots subreddit "
                                  "or their discord server(Invite: xRFmHYQ)")

            await default_channel.send(embed=embed)
    # endregion
