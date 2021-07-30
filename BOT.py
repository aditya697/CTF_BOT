from keep_alive import keep_alive
from datetime import *
from dateutil.parser import parse
import re
import discord
import requests
import sys

client = discord.Client()

ctfs = {}

def useful():
    now = datetime.utcnow()
    unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0',
    }
    upcoming = 'https://ctftime.org/api/v1/events/'
    limit = '5'  # Max amount I can grab the json data for
    response = requests.get(upcoming, headers=headers, params=limit)
    jdata = response.json()

    for num, i in enumerate(jdata):  # Generate list of dicts of upcoming ctfs
        ctf_title = jdata[num]['title']
        (ctf_start, ctf_end) = (parse(jdata[num]['start'].replace('T', ' ').split('+', 1)[0]),
                                parse(jdata[num]['finish'].replace('T', ' ').split('+', 1)[0]))
        (unix_start, unix_end) = (
            int(ctf_start.replace(tzinfo=timezone.utc).timestamp()),
            int(ctf_end.replace(tzinfo=timezone.utc).timestamp()))
        dur_dict = jdata[num]['duration']
        (ctf_hours, ctf_days) = (str(dur_dict['hours']), str(dur_dict['days']))
        ctf_link = jdata[num]['url']
        ctf_image = jdata[num]['logo']
        ctf_format = jdata[num]['format']
        ctf_place = jdata[num]['onsite']
        if ctf_place == False:
            ctf_place = 'Online'
        else:
            ctf_place = 'Onsite'

        ctf = {
            'name': ctf_title,
            'start': unix_start,
            'end': unix_end,
            'dur': ctf_days + ' days, ' + ctf_hours + ' hours',
            'url': ctf_link,
            'img': ctf_image,
            'format': ctf_place + ' ' + ctf_format
        }
        ctfs[ctf_title] = ctf

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == "help":
        embed = discord.Embed(title="Help on Bot", description="Some useful commands")
        embed.add_field(name="ctf upcoming", value="For upcoming ctfs.")
        embed.add_field(name="ctf ongoing", value="For ongoing ctfs")
        embed.add_field(name="leaderboard",value="The top 10 teams in the world.")
        embed.add_field(name="timeleft",value="The remaining time for ctf to end.")
        embed.add_field(name="countdown",value="The time for ctf to start.")
        await message.channel.send(content=None, embed=embed)    

    elif message.content == ("ctf upcoming"):
        amount = '3'
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0',
        }
        upcoming_ep = "https://ctftime.org/api/v1/events/"
        default_image = "https://pbs.twimg.com/profile_images/2189766987/ctftime-logo-avatar_400x400.png"
        r = requests.get(upcoming_ep, headers=headers, params=amount)
        # print("made request")

        upcoming_data = r.json()

        for ctf in range(0, int(amount)):
            ctf_title = upcoming_data[ctf]["title"]
            (ctf_start, ctf_end) = (upcoming_data[ctf]["start"].replace("T", " ").split("+", 1)[0] + " UTC",
                                    upcoming_data[ctf]["finish"].replace("T", " ").split("+", 1)[0] + " UTC")
            (ctf_start, ctf_end) = (re.sub(":00 ", " ", ctf_start), re.sub(":00 ", " ", ctf_end))
            dur_dict = upcoming_data[ctf]["duration"]
            (ctf_hours, ctf_days) = (str(dur_dict["hours"]), str(dur_dict["days"]))
            ctf_link = upcoming_data[ctf]["url"]
            ctf_image = upcoming_data[ctf]["logo"]
            ctf_format = upcoming_data[ctf]["format"]
            ctf_place = upcoming_data[ctf]["onsite"]
            if ctf_place == False:
                ctf_place = "Online"
            else:
                ctf_place = "Onsite"

            embed = discord.Embed(title=ctf_title, description=ctf_link, color=int("f23a55", 16))
            if ctf_image != '':
                embed.set_thumbnail(url=ctf_image)
            else:
                embed.set_thumbnail(url=default_image)

            embed.add_field(name="Duration", value=((ctf_days + " days, ") + ctf_hours) + " hours", inline=True)
            embed.add_field(name="Format", value=(ctf_place + " ") + ctf_format, inline=True)
            embed.add_field(name="Timeframe", value=(ctf_start + " -> ") + ctf_end, inline=True)
            await message.channel.send(content=None, embed=embed)

    elif message.content == ('leaderboard'):
        year = str(datetime.today().year)
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0',
        }
        top_ep = f"https://ctftime.org/api/v1/top/{year}/"
        leaderboards = ""
        r = requests.get(top_ep, headers=headers)
        if r.status_code != 200:
            await message.send("Error retrieving data, please report this with `>report \"what happened\"`")
        else:
            try:
                top_data = (r.json())[year]
                for team in range(10):
                    rank = team + 1
                    teamname = top_data[team]['team_name']
                    score = str(round(top_data[team]['points'], 4))

                    if team != 9:
                        leaderboards += f"\n[{rank}]    {teamname}: {score}"
                    else:
                        leaderboards += f"\n[{rank}]   {teamname}: {score}\n"

                await message.channel.send(
                    f":triangular_flag_on_post:  **{year} CTFtime Leaderboards**```ini\n{leaderboards}```")
            except KeyError as e:
                await message.channel.send("Please supply a valid year.")

    elif message.content == ("ctf ongoing"):
        useful()
        now = datetime.utcnow()
        unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
        running = False

        for title in ctfs:
            ctf = ctfs.get(title)
            if ctf['start'] < unix_now and ctf['end'] > unix_now:  # Check if the ctf is running
                running = True
                embed = discord.Embed(title=':red_circle: ' + ctf['name'] + ' IS LIVE', description=ctf['url'],
                                      color=15874645)
                start = datetime.utcfromtimestamp(ctf['start']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
                end = datetime.utcfromtimestamp(ctf['end']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
                if ctf['img'] != '':
                    embed.set_thumbnail(url=ctf['img'])
                else:
                    embed.set_thumbnail(
                        url="https://pbs.twimg.com/profile_images/2189766987/ctftime-logo-avatar_400x400.png")
                    # CTFtime logo

                embed.add_field(name='Duration', value=ctf['dur'], inline=True)
                embed.add_field(name='Format', value=ctf['format'], inline=True)
                embed.add_field(name='Timeframe', value=start + ' -> ' + end, inline=True)
                await message.channel.send(embed=embed)

        if running == False:  # No ctfs were found to be running
            await message.channel.send(
                "No CTFs currently running! Check out >ctftime countdown, and >ctftime upcoming to see when ctfs will start!")
    
    elif message.content == ("timeleft"):
      useful()
      now = datetime.utcnow()
      unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
      running = False
      for title in ctfs:
          ctf = ctfs.get(title)
          if ctf['start'] < unix_now and ctf['end'] > unix_now:  # Check if the ctf is running
              running = True
              time = ctf['end'] - unix_now
              days = time // (24 * 3600)
              time = time % (24 * 3600)
              hours = time // 3600
              time %= 3600
              minutes = time // 60
              time %= 60
              seconds = time
              embed = discord.Embed(title=':red_circle: ' + ctf['name'] + ' IS LIVE', description=ctf['url'],color=15874645)
              if ctf['img'] != '':
                  embed.set_thumbnail(url=ctf['img'])
              else:
                  embed.set_thumbnail(
                  url="https://pbs.twimg.com/profile_images/2189766987/ctftime-logo-avatar_400x400.png")                        
              await message.channel.send(
                  f"```ini\n{ctf['name']} ends in: [{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]```\n")
              await message.channel.send(embed=embed) 
      if running == False:
          await message.channel.send('No ctfs are running! Use >ctftime upcoming or >ctftime countdown to see upcoming ctfs')

    elif message.content == ("countdown"):
      useful()
      now = datetime.utcnow()
      unix_now = int(now.replace(tzinfo=timezone.utc).timestamp())
      # TODO: make this a function, too much repeated code here.
      for title in ctfs:
        ctf = ctfs.get(title)
        start = datetime.utcfromtimestamp(ctf['start']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'
        end = datetime.utcfromtimestamp(ctf['end']).strftime('%Y-%m-%d %H:%M:%S') + ' UTC'

        time = ctf['start'] - unix_now
        days = time // (24 * 3600)
        time = time % (24 * 3600)
        hours = time // 3600
        time %= 3600
        minutes = time // 60
        time %= 60
        seconds = time

        embed = discord.Embed(title=':red_circle: ' + ctf['name'] + ' IS LIVE', description=ctf['url'],color=15874645)
        if ctf['img'] != '':
          embed.set_thumbnail(url=ctf['img'])
        else:
            embed.set_thumbnail(
            url="https://pbs.twimg.com/profile_images/2189766987/ctftime-logo-avatar_400x400.png")
        await message.channel.send(f"```ini\n{ctf['name']} ends in: [{days} days], [{hours} hours], [{minutes} minutes], [{seconds} seconds]```\n")
        await message.channel.send(embed=embed)      

keep_alive()
client.run('DISCORD TOKEN')
