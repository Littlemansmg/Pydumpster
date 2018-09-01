"""
logs cog
"""

from datetime import datetime as dt
import logging

logging.basicConfig(
    handlers=[logging.FileHandler('discord.log', 'a', 'utf-8')],
    level=logging.INFO
)

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

def guildinfo(reason, gid):
    now = dt.now().strftime('%m/%d %H:%M')
    logging.info(f'{now} Guild: {gid}, {reason}')

# endregion