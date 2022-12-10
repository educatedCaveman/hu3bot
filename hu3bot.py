import discord
from discord.ext import commands
import requests
import datetime
import os
from dotenv import load_dotenv
import math
import asyncio

# attempt to evaluate secrets either from a .env file or from docker secrets.
# https://stackoverflow.com/questions/65447044/python-flask-application-access-to-docker-secrets-in-a-swarm/66717793#66717793

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)


def manage_secrets(name):
    var1 = os.getenv(name)
    
    secret_path = f'/run/secrets/{name}'
    existence = os.path.exists(secret_path)
    
    if var1 is not None:
        return var1
    
    if existence:
        var2 = open(secret_path).read().rstrip('\n')
        return var2
    
    if all([var1 is None, not existence]):
        return KeyError(f'{name}')

load_dotenv()
# DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_TOKEN = manage_secrets(name='DISCORD_TOKEN')

print(DISCORD_TOKEN)

DISCORD_CHANNEL = os.getenv('DISCORD_CHANNEL')
PRINTER_HOST = os.getenv('PRINTER_HOST')
CAM_PORT_MAIN = os.getenv('CAM_PORT_MAIN')
CAM_PORT_ALT = os.getenv('CAM_PORT_ALT')
MOONRAKER_API_PORT = os.getenv('MOONRAKER_API_PORT')
WEB_URL = os.getenv('WEB_URL')


bot_intents = discord.Intents.default()
bot_intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=bot_intents)

@bot.event
async def on_ready():
    print(f'hu3bot is ready!')
    # print(DISCORD_TOKEN)
    #TODO: put a constant check of the printer status here?


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


def to_lower(arg):
    return arg.lower()


@bot.command(name='snapshot', aliases=['snapshit'])
async def snapshot(context, *, cam:to_lower='main'):
    """
    takes a snapshot

    Parameters
    -----------
    cam : str, optional
        which camera is used (main, alt, or both)
    """
    if cam in ['main', 'alt']:
        snapshot = capture_snapshot(cam)
        embed = discord.Embed()
        base_name = snapshot.split('/')[-1]
        file = discord.File(snapshot, filename=base_name)
        embed.set_image(url=f"attachment://{base_name}")
        await context.send(file=file)

    elif cam == 'both':
        embeds = []
        files = []
        for i in ['main', 'alt']:
            embed = discord.Embed()
            snapshot = capture_snapshot(i)
            base_name = snapshot.split('/')[-1]
            file = discord.File(snapshot, filename=base_name)
            files.append(file)
            embed.set_image(url=f"attachment://{base_name}")
            embeds.append(embed)
            # need to sleep so the file names are different
            await asyncio.sleep(1)

        await context.send(files=files)

    else:
        message = f"""unrecognized argument:\t`{cam}`"""
        await context.send(message)


# @bot.command(name='test')
# async def test(context):
#     """
#     basic test/debugging command
#     """
#     await context.send(content="I'm not quite dead yet!  I don't want to go on the cart!")



def get_from_moonraker(api:str=None):
    URL = f"http://{PRINTER_HOST}:{MOONRAKER_API_PORT}/{api}"
    response = requests.get(URL)
    data = response.json()
    return data


def time_fmt(secs:float):
    hours = str(math.floor(secs / 3600))
    mins = str(math.floor((secs % 3600) / 60)).zfill(2)
    return f"{hours}h:{mins}m"


@bot.command(name='status')
async def status(context, *, stus:to_lower=None):
    # https://moonraker.readthedocs.io/en/latest/web_api/#printer-status
    # basic print stats

    print_stats_api = 'printer/objects/query?print_stats'
    print_stats = get_from_moonraker(print_stats_api)['result']['status']['print_stats']
    state = print_stats['state']

    display_stats_api = 'printer/objects/query?display_status'
    display_stats = get_from_moonraker(display_stats_api)['result']['status']['display_status']
    progress = display_stats['progress']
    prog_pct = round(progress * 100, 1)

    #state is one of: standby, printing, paused, error, complete
    state_colors = {
        'printing':     discord.Colour.brand_green(),
        'complete':     discord.Colour.brand_green(),
        'standby':      discord.Colour.blue(),
        'paused':       discord.Colour.yellow(),
        'error':        discord.Colour.brand_red(),
    }
    
    embed = discord.Embed(
        title = f"{state.title()}",
        type = "rich",
        description = f"{prog_pct}% complete",
        url = WEB_URL,
        color = state_colors[state]
    )

    if stus is None:
        await context.send(embed=embed)

    elif stus == 'detailed':
        # filename
        embed.add_field(name='file', value=print_stats['filename'], inline=False)

        # print time, total time, filament used
        embed.add_field(name='print time', value=time_fmt(print_stats['print_duration']), inline=True)
        embed.add_field(name='total time', value=time_fmt(print_stats['total_duration']), inline=True)
        filament_fmt = f"{round((print_stats['filament_used'] / 1000), 3)} m"
        embed.add_field(name='filament used', value=filament_fmt, inline=True)

        # estimated totals
        est_embed = discord.Embed(
            title = "Estimated Totals:",
            type = "rich",
            color = state_colors[state]
        )
        est_duration = print_stats['print_duration'] / progress
        est_total = print_stats['total_duration'] / progress
        est_filament = f"{round((print_stats['filament_used'] / 1000) / progress, 3)} m"
        est_embed.add_field(name='print time', value=time_fmt(est_duration), inline=True)
        est_embed.add_field(name='total time', value=time_fmt(est_total), inline=True)
        est_embed.add_field(name='filament used', value=est_filament, inline=True)

        await context.send(embeds=[embed, est_embed])
    
    else:
        message = f"""unrecognized argument:\t`{stus}`"""
        await context.send(message)


#TODO: reset the stats


@bot.command(name='info')
async def status(context):
    pass



bot.run(DISCORD_TOKEN)
