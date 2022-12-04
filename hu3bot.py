import discord
from discord.ext import commands
import requests
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL = os.getenv('DISCORD_CHANNEL')
PRINTER_HOST = os.getenv('PRINTER_HOST')
CAM_PORT_MAIN = os.getenv('CAM_PORT_MAIN')
CAM_PORT_ALT = os.getenv('CAM_PORT_ALT')


bot_intents = discord.Intents.default()
bot_intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=bot_intents)


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
    await context.send(content="BTW, you should use !snapshot, not !snapshit.")


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


print(f'discord_token: {DISCORD_TOKEN}')
bot.run(DISCORD_TOKEN)