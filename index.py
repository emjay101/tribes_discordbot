from typing import Callable
import discord
from  tribes import  discord_get_serverinfo
import logging

############# CONFIG START ####################

#e.g. AAAAAAAAAAAAAAAAAAAAAAAA.AAAAAA.AAAAAAAAAAAAAAAAAAAAAA_AAAA
DISCORD_AUTH_TOKEN = "ADD_AUTH_TOKEN"

discord_observed_channels = {
    #respond to all channels in here
    "880469577639788694":True,
    "880469511814398025":True,
    "ADD_CHANNEL_HERE":True
}

discord_commands = {
        #"chat_cmd":        (function,               ip, port, color in rgb)
        "!lt":(discord_get_serverinfo, "207.148.13.132", 28006, 0xa00264),
        "!pu":(discord_get_serverinfo, "207.148.13.132", 28001, 0x737ecd)
}
############# CONFIG END ####################

client = discord.Client()

@client.event
async def on_ready():
    logging.info('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global discord_observed_channels, discord_commands
    if message.author == client.user:
        return

    if message.channel.id is None:
        return

    if discord_observed_channels is None or len(discord_observed_channels) == 0 or not discord_observed_channels.get("%s" % (message.channel.id,), False):
        return

    msg_content = (message.content or "").strip()
    if not msg_content.startswith("!"):
        return

    func = discord_commands.get(msg_content)
    if func and len(func) > 2 and isinstance(func[0], Callable):
        try:
            res = await func[0](func[1], func[2])
            if  res:
                outname = []
                if res.password:
                    outname.append("🔒")
                outname.append(res.serverName)
                embedVar = discord.Embed(title=" ".join(outname), description="%d/%d" % (res.playerCount, res.maxPlayers,), color=func[3])
                embedVar.add_field(name=res.missionName, value="%s / %s" % (res.modName,res.missionType), inline=False)

                for team in res.teams.keys():
                    players = ",".join([tmpval[4] for tmpval in res.teams.get(team,("", None, -3, []))[3] if len(tmpval) > 3 ])
                    if len(players) > 0:
                        embedVar.add_field(name=res.teams[team][0], value=players, inline=False)
                #embedVar.set_footer(name="footer")
                await message.channel.send(embed=embedVar)
        except:
            logging.exception(msg_content)

logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO)
client.run(DISCORD_AUTH_TOKEN)
