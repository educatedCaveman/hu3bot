import discord
from discord.ext import commands
import requests
import datetime
import os
from dotenv import load_dotenv
import math
import asyncio
from tabulate import tabulate
import pprint

# attempt to evaluate secrets either from a .env file or from docker secrets.
# https://stackoverflow.com/questions/65447044/python-flask-application-access-to-docker-secrets-in-a-swarm/66717793#66717793

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)


def manage_secrets(name:str):
    """
    will evaluate secrets from either environment variables or docker
    secrets. (assumed to be /run/secrets/<secret_name>)

    Parameters
    -----------
    name : str
        name of the secret

    Returns
    -----------
    str
        the value of the secret
    KeyError
        exception 
    """
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
DISCORD_TOKEN = manage_secrets(name='HU3BOT_DISCORD_TOKEN')
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
    """
    runs when the bot is ready
    """
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
    snapshot = f"/tmp/snapshot_{datetime.datetime.now().strftime('%F-%T.%f')}.jpeg"
    print(f'capturing snapshot: {snapshot}')
    response = requests.get(URL)
    open(snapshot, 'wb').write(response.content)

    return snapshot


def to_lower(arg):
    """
    wrapper for making a string all lower-case

    Parameters
    -----------
    arg : str
        text to lower-case

    Returns
    -----------
    str
        input text in lower-case
    """
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
            # await asyncio.sleep(1)

        await context.send(files=files)

    else:
        message = f"""unrecognized argument:\t`{cam}`"""
        await context.send(message)


async def catch_moonraker_error(context, resp):
    """
    checks for a successful moonraker API call, and sends a message
    on failure, describing said failure.

    Parameters
    -----------
    context:
        bot context
    resp:
        the requests.Response() object

    Returns
    -----------
    bool
        was the request to moonraker successful?
    """
    if isinstance(resp, requests.models.Response):
        # await context.send('request is valid')
        return False
    else:
        if isinstance(resp, requests.exceptions.Timeout):
            await context.send(f'response is a timeout exception:\n```{resp}```')
        if isinstance(resp, requests.exceptions.TooManyRedirects):
            await context.send(f'response is a redirect exception:\n```{resp}```')
        if isinstance(resp, requests.exceptions.RequestException):
            await context.send(f'response is a request exception:\n```{resp}```')
        else:
            await context.send(f'respnse is something else:\n```{resp}```')

        return True


def get_from_moonraker(api:str=None):
    """
    performs an API call to moonraker

    Parameters
    -----------
    api : str , optional
        the api object to query

    Returns
    -----------
    requests.Response()
        the response to the request
    Exception
        any exception thrown during the API call
    """
    #check for nothing being passed:
    if api is None:
        return api

    try:
        URL = f"http://{PRINTER_HOST}:{MOONRAKER_API_PORT}/{api}"
        response = requests.get(URL)
        return response
    except Exception as e:
        return e


def time_fmt(secs:float):
    """
    formats seconds in the hh:mm format

    Parameters
    -----------
    secs : float
        number of seconds

    Returns
    -----------
    str
        formatted time
    """
    hours = math.floor(secs / 3600)
    hours_fmt = "{:,}".format(hours)
    mins = str(math.floor((secs % 3600) / 60)).zfill(2)
    return f"{hours_fmt}h : {mins}m"


@bot.command(name='status')
async def status(context, *, stus:to_lower=None):
    """
    printer status

    Parameters
    -----------
    context :
        the event context
    stus : str, optional
        the type of status to return. can be missing or "detailed"

    """
    # https://moonraker.readthedocs.io/en/latest/web_api/#printer-status
    # basic print stats

    print_stats_api = 'printer/objects/query?print_stats'
    api_resp = get_from_moonraker(print_stats_api)
    if await catch_moonraker_error(context=context, resp=api_resp):
        return
    print_stats = api_resp.json()['result']['status']['print_stats']
    state = print_stats['state']

    display_stats_api = 'printer/objects/query?display_status'
    api_resp = get_from_moonraker(display_stats_api)
    if await catch_moonraker_error(context=context, resp=api_resp):
        return
    display_stats = api_resp.json()['result']['status']['display_status']
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


def split_string(line:str, max_len:int=70):
    """
    splits a string into a list of shorter strings

    The input string is split via spaces, and said space is removed.
    The space chosen is the last one in the first <max_len> chars in
    the text still needing to be split.

    Parameters
    -----------
    line : str
        the string to be split over multiple lines
    max_len : int , optional
        the maximum length of the lines being split. defaults to 70

    Returns
    -----------
    list
        input string split into "lines"
    """
    if len(line) <= max_len:
        tmp_list = [line.strip()]
        return tmp_list

    else:
        all_indexes = [x for x, v in enumerate(line) if v == ' ']
        short_indexes = list(filter(lambda index: index <= max_len, all_indexes))
        max_space = max(short_indexes)
        short_line = [line[:max_space]]
        remainder = line[max_space:].strip()
        short_line.extend(split_string(remainder))
        return short_line


def dict_to_table(json_dict:dict, max_len:int=70, compact:bool=False, last:bool=False):
    """
    converts a dictionary/json into a formatted table for discord

    Parameters
    -----------
    json_dict : dict
        the input data to format
    max_len : int , optional
        the maximum length of the formatted values
    compact : bool , optional
        print the values in a compact manner of not
    last : bool , optional
        continue recursing or not.

    Returns
    -----------
    str
        a tabluate table formatted into a discord message text
    """
    table = []
    pp = pprint.PrettyPrinter(indent=4, compact=compact, width=max_len)
    for key in json_dict:
        value = json_dict[key]

        # format list-like types
        if isinstance(value, dict) or \
                isinstance(value, list) or \
                isinstance(value, tuple):
            if compact:
                value = "[...]"
            else:
                value = pp.pformat(value)
        
        # handle long value strings
        elif len(str(value)) > max_len:
            # value isn't already a string, convert it
            if not isinstance(value, str):
                value = str(value)
            value = "\n".join(split_string(line=value, max_len=max_len))

        table.append([key, value])

    # check length of table as a string:
    fmt_table = f"```{tabulate(table, ['key', 'value'], tablefmt='fancy_grid')}```"
    if len(str(fmt_table)) > 2000:
        # rerun the function but make things compact, if we haven't already re-run it
        if compact and last:
            warning = "the following was truncated:\n"
            full_message = warning + fmt_table
            truncated = full_message[:1997] + "```"
            return truncated
        else:
            fmt_table = dict_to_table(json_dict=json_dict, max_len=max_len, compact=True, last=True)

    return fmt_table


@bot.command(name='info')
async def info(context, *, info_req:to_lower=None):
    """
    information about printer objects

    objects can be queried by running `!info <object_name>`. Many objects
    will have sub-sections. When possible, these will also be printed 
    when querying top-level objects. If they cannot be printed, they will
    be shown as `[...]`. These lower-level objects can be queried by
    running `!info <object_name>/<sub_object>`.

    Parameters
    -----------
    context:
        event context
    info_req : str , optional
        the requested information section.
        sections.
    """

    # *SETUP
    # all printer object, with some filters
    obj_api = 'printer/objects/list'
    api_resp = get_from_moonraker(api=obj_api)
    if await catch_moonraker_error(context=context, resp=api_resp):
        return
    # disect the response
    objects = api_resp.json()['result']['objects']
    obj_list = []
    omit_strings = ['gcode_macro', 'configfile', ]
    for obj in objects:
        skip = False
        for omit in omit_strings:
            if obj.startswith(omit):
                skip = True
        if not skip:
            obj_list.append(obj)

    # *CASE 1
    # when no argument provided
    if info_req is None:
        msg = "The following printer objects can be queried:\n\n```"
        for obj in obj_list:
            msg += f"{obj}\n"
        msg += "```\nto query these, type `!info <item>`"
        await context.send(msg)
    
    # *CASE 2
    # some argument provided
    # assumed to be a single request
    else:
        args = info_req.split('/')
        arg = args[0]

        # for arg in args:
        api_path = f'printer/objects/query?{arg}'
        api_resp = get_from_moonraker(api=api_path)
        if await catch_moonraker_error(context=context, resp=api_resp):
            return

        tmp_json_resp = api_resp.json()['result']['status'][arg]
        api_resp = tmp_json_resp
        if len(args) > 1:
            for sub_arg in args:
                if sub_arg != arg:
                    api_resp = api_resp[sub_arg]

        resp = dict_to_table(api_resp)
        await context.send(resp)



#TODO: reset the stats
@bot.command(name='history', aliases=['jobs'])
async def history(context, *, details:to_lower=None):
    """
    converts a dictionary/json into a formatted table for discord

    Parameters
    -----------
    context : 
        the event context
    details : str , optional
        the sub-command. 
    """

    #*default: just some high-level history stats
    if details is None:
        job_hist = 'server/history/list?limit=10'
        api_resp = get_from_moonraker(job_hist)
        if await catch_moonraker_error(context=context, resp=api_resp):
            return
        hist_stats = api_resp.json()['result']['jobs']

        hist_data = []
        for job in hist_stats:
            row = [
                job['filename'].split('/')[-1],
                f"{round(job['filament_used'] / 1000, 1)}m",
                time_fmt(job['print_duration']),
                job['status']
            ]
            hist_data.append(row)

        headers = ['file', 'filament', 'time', 'status']
        fmt_table = f"{tabulate(hist_data, headers, tablefmt='fancy_grid')}"
        print(fmt_table)
        msg = f"```{fmt_table}```"
        await context.send(msg)

    #*job totals
    elif details.startswith('total'):
        # reset the job totals:
        if details.startswith('total reset'):
            pass
            #TODO: use the wait for response in order to confirm the reset?
        else:
            totals_api = "server/history/totals"
            api_resp = get_from_moonraker(totals_api)
            if await catch_moonraker_error(context=context, resp=api_resp):
                return
            job_totals = api_resp.json()['result']['job_totals']
            filament_fmt = round(job_totals['total_filament_used'] / 1000)

            totals_fmt = [
                ['total jobs', job_totals['total_jobs']],
                ['total job time', time_fmt(job_totals['total_time'])],
                ['total print time', time_fmt(job_totals['total_print_time'])],
                ['filament used', "{:,}".format(filament_fmt) + " m"],
                ['longest job', time_fmt(job_totals['longest_job'])],
                ['longest print', time_fmt(job_totals['longest_print'])],
            ]
            fmt_table = f"{tabulate(totals_fmt, ['job stat', 'value'], tablefmt='fancy_grid')}"
            msg = f"```{fmt_table}```"
            await context.send(msg)


#*Run the bot
bot.run(DISCORD_TOKEN)
