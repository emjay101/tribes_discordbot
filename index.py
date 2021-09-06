from typing import Callable
import discord
from  tribes import TribesMasterClient
import logging

#e.g. AAAAAAAAAAAAAAAAAAAAAAAA.AAAAAA.AAAAAAAAAAAAAAAAAAAAAA_AAAA
DISCORD_TOKEN = ""

#respond to all channels in here
discord_observed_channels = {
    "880469577639788694":True,
    "880469511814398025":True,
}

_debug_log = logging.getLogger(__name__)

async def discord_get_serverinfo(ip, port):
    global _debug_log
    tribes_srv = None
    try:
        tribes_srv = TribesMasterClient(ip, port)
        try:
            await tribes_srv.Query(readplayerdata=True)
        except:
            tribes_srv.logger.exception()
    except:
        _debug_log.exception("%s %s" % (ip, port))
    return tribes_srv

discord_commands = {
        #"chat_cmd":(function, ip, port, color in rgb)
        "!lt":(discord_get_serverinfo, "207.148.13.132", 28006, 0xa00264),
        "!pu":(discord_get_serverinfo, "207.148.13.132", 28001, 0x737ecd)
}

client = discord.Client()

@client.event
async def on_ready():
    global   _debug_log
    _debug_log.info('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global discord_observed_channels, discord_commands, _debug_log
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
            _debug_log.exception(msg_content)

client.run(DISCORD_TOKEN)
