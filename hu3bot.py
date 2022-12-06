import discord
from discord.ext import commands
import requests
import datetime
import os
from dotenv import load_dotenv
# import json
# import time
# import threading

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL = os.getenv('DISCORD_CHANNEL')
PRINTER_HOST = os.getenv('PRINTER_HOST')
CAM_PORT_MAIN = os.getenv('CAM_PORT_MAIN')
CAM_PORT_ALT = os.getenv('CAM_PORT_ALT')
MOONRAKER_BOT_ID = os.getenv('MOONRAKER_BOT_ID')


bot_intents = discord.Intents.default()
bot_intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=bot_intents)


def capture_snapshot(cam='main'):
    """
    Takes and saves the snapshot.  Handles which camera to use for the snapshot.

    Parameters
    -----------
    cam : str, optional
        which camera is used (main xor alt)

    Returns
    -----------
    str
        the path of the saved screenshot
    """
    if cam == 'main':
        URL = f"http://{PRINTER_HOST}:{CAM_PORT_MAIN}/?action=snapshot"
    else:
        URL = f"http://{PRINTER_HOST}:{CAM_PORT_ALT}/?action=snapshot"
    snapshot = f"/tmp/snapshot_{datetime.datetime.now().strftime('%F-%T')}.jpeg"
    print(f'capturing snapshot: {snapshot}')
    response = requests.get(URL)
    open(snapshot, 'wb').write(response.content)

    return snapshot


@bot.command(name='snapshot')
async def snapshot(context, cam='main'):
    """
    takes a snapshot

    Parameters
    -----------
    cam : str, optional
        which camera is used (main xor alt)
    """
    snapshot = capture_snapshot(cam)
    embed = discord.Embed()
    base_name = snapshot.split('/')[-1]
    file = discord.File(snapshot, filename=base_name)
    embed.set_image(url=f"attachment://{base_name}")
    await context.send(file=file)


@bot.command(name='snapshit')
async def snapshit(context, cam='main'):
    """
    alias for common typo of !snapshot

    Parameters
    -----------
    cam : str, optional
        which camera is used (main xor alt)

    See Also
    --------
    snapshot : takes a snapshot
    """
    await snapshot(context, cam)
    await context.send(content="BTW, you should use /snapshot, not /snapshit.")


@bot.command(name='test')
async def snapshit(context):
    """
    basic test/debugging command
    """
    await context.send(content="I'm not quite dead yet!  I don't want to go on the cart!")


@bot.event
async def on_message(message):
    """
    Listens to all messages on the channel, and will invoke snapshot() when it
    sees the phrase "Your printer completed printing".  This should really
    only be seen from the Moonraker completion notification.

    I know this is a bad way to do this, but I've been unable to figure out
    how to get this bot to listen to !commands from other bots.  This current
    solution should be sufficient enough given the phrase is long, uncommon, 
    and it must be posted in a specific channel by a bot.
    """
    ctx = await bot.get_context(message)
    await bot.invoke(ctx)
    if message.channel.name == DISCORD_CHANNEL \
            and message.author.bot \
            and 'Your printer completed printing' in message.content:
        await snapshot(ctx)



async def print_status(context):
    URL = "http://192.168.11.10:7125/printer/objects/query?print_stats"
    response = requests.get(URL)
    data = response.json()
    status = data['result']['status']['print_stats']['state']
    await context.send(content=status)


# listen for moonraker bot messages
@bot.event
async def on_message(message):
    if message.author != bot.user \
            and message.channel.name == DISCORD_CHANNEL \
            and message.author != MOONRAKER_BOT_ID:
        context = await bot.get_context(message)
        await bot.invoke(context)
        await print_status(context)
        # msg = f"{message.author} != {MOONRAKER_BOT_ID}"
        # await message.channel.send(content=msg)
        # msg = f"author.name: {message.author.name}.  author.id: {message.author.id}"
        # await message.channel.send(content=msg)

    # context = await bot.get_context(message)
    # await bot.invoke(context)
    # await message.channel.send(message.author)


# listen for messages from moonraker
@bot.event
async def on_message(message):
    if message.author.id == MOONRAKER_BOT_ID:
        context = await bot.get_context(message)
        await bot.invoke(context)
        await print_status(context)



bot.run(DISCORD_TOKEN)


# t1 = threading.Thread(target=bot.run(DISCORD_TOKEN))  
# t2 = threading.Thread(target=wait_for_status())  
# t1.start()
# t2.start()

