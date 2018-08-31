# Pydumpster
This bot is built to follow subreddits and send posts to a discord server. This is a remake of 
[Pydump-async](www.github.com/littlemansmg/pydump-async).

## Getting Started
[Invite](https://discordapp.com/api/oauth2/authorize?client_id=416449905805230080&permissions=125968&scope=bot) 
the bot to your server! It's constantly maintained, and running.

## Current Functionality
* Bot can access Reddit's json object of a subreddit.
* Bot can sort through the json object to find the proper URL and send the URL + the subreddit it came from to discord. 
* Bot can read server settings from json file.
* Bot can set various options
  * Default channel
    * Where the bot should send reddit posts
    * Default channel is the server owner
  * NSFW filter
    * Filters out what reddit has flaged as over 18 content
    * Default on
    * Toggleable
  * Create channels
    * This option will set if the bot can create a channel for each subreddit it's watching
    * Default off
    * Toggleable
  * Set valid subreddits to 'subscribe' to
    * List of reddits for the bot to check for post from
    * Defaulted to an empty list
  * Set default delay inbetween posts
    * Time (in seconds) how often the bot posts.
    * Defaulted to 5 minutes
* Bot can add/remove a server with set defaults with no user interaction
* All major commands i.e. sub, unsub, toggle nsfw/create are admin only commands

## TODO
*This list is in no particular order.*
* Add more options. (planned below)
  * default sort
* add text to the regular text posts
* add a better suggestion method
* Set up role based checks. 
  * Ex. Instead of just admins, let people with x role use the command.

## Known Issues
* Most gifs don't load in the embeds, so it forces the user to go to reddit itself to view.
* If a title or a text value is too long, it will error and repost multiple times before fixing itself. 

## Built With
* [Discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper to run a discord bot in Python.
  * version 1.0.0 A.K.A. [discord-rewrite.py](https://discordpy.readthedocs.io/en/rewrite/index.html).
  Most of this is the documentation for discord.ext.commands
