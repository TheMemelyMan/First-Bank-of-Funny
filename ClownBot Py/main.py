import discord
from discord.ext import commands
from discord.utils import get
import random
import json
import discord.ext.commands
from pymongo import MongoClient
import time
import threading
from discord.voice_client import VoiceClient

with open('config.json') as f:
    configData = json.load(f)
with open('chatlog.json') as g:
    chatData = json.load(g)


prefix = configData["information"][0]["prefix"]
mongoPath = configData["tokens"][0]["mongoPath"]

client = MongoClient(mongoPath)

#database clients
dbDiscord = client['Discord']

description = '''Clowbot commands and such. Ping Memely if you need any help'''
bot = commands.Bot(command_prefix=prefix, description=description)

class Main_Commands():
    def __init__(self, bot):
        self.bot = bot

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

"""logging"""
@bot.event
async def on_message(message):

    print(f"Message Content:\n{message.content}")
    try:
        print(message.attachments[0].url)
    except IndexError:
        pass
    print(f"             User: {message.author.name}")
    print(f"          Channel: {message.channel.name}")
    print(f"      Message URL: {message.jump_url}")
    print(f"       Message ID: {message.id}")
    print(f"          User ID: {message.author.id}")
    print("-----------------------------------")

    ID = str(message.guild.id)

    content = message.content
    

    
    try:
        content += " : " + message.attachments[0].url
    except IndexError:
        pass
    user = message.author.name
    channel = message.channel.name
    messageURL = message.jump_url
    messageID = message.id
    userID = message.author.id

    posts = dbDiscord[ID]


    post_data = {
    'content': content,
    'User': user,
    'Channel': channel,
    'Message URL': messageURL,
    'message ID': messageID,
    'User ID': userID
    }
    try:
        new_result = posts.insert_one(post_data)
    except:
        print("Did not post to DB successfully")

    
    await bot.process_commands(message)
    
    """async for messages in message.channel.history():
        print(messages.content)"""

@bot.command()
async def commandHelp(ctx):

    embed=discord.Embed(title="Command Help")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/387432001180925953/591601803033051136/hcc-avatar.png")

    embed.add_field(name="!getShare", value="Posts a link to a voice chat you are in for screen sharing and webcam calls", inline=False)
    embed.add_field(name="!requestBanner <image link> <name (one word)>", value="Sends banners off to a queue for admins to double check before putting them into an approved queue", inline=False)
    embed.add_field(name="!displayBannerQueue", value="Displays both the request banner queue and the mod approved queue", inline=False)
    embed.add_field(name="!commandHelp", value="Displays help dialogues for ClownBot commands", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def getShare(ctx):
    """Posts a link to a voice chat you are in for screen sharing and webcam calls"""
    if (ctx.message.author.voice.channel is not None):
        voiceChannelName = str(ctx.guild.get_channel(ctx.message.author.voice.channel.id))
        voiceChannelID = str(ctx.message.author.voice.channel.id)
        serverID = str(ctx.guild.id)
        commanderName = str(ctx.message.author)

        embed=discord.Embed(title="Voice call screenshare and camera link for " + voiceChannelName, color=0x97a7d2)
        embed.set_author(name=commanderName)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/229820513738948609/590028508147744798/sig-4036785.png")
        embed.add_field(name='Current Voice Chat: ' + voiceChannelName, value='Voice Chat ID: ' + voiceChannelID, inline=False)
        embed.add_field(name='Video Call Link', value="["+ voiceChannelName +"](http://www.discordapp.com/channels/" + serverID + "/" + voiceChannelID + ")", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("You aren't in a voice chat, clown")

@bot.command()
async def funny(ctx, UID:int, role:str):
    if(ctx.author.id == 380801506137473034):
        try:
            for u in ctx.guild.members:
                if(int(u.id) == UID):
                    member = u
                    break
            for r in member.roles:
                if(str(r) == role):
                    print("Removing role: " + str(r))
                    await member.remove_roles(r)
                    break
        except Exception as e:
            print(e)
            print("Didnt work")
    else:
        await ctx.send("You're not funny enough")

@bot.command()
async def unfunny(ctx, UID:int, role:str):
    if(ctx.author.id == 380801506137473034):
        try:
            for u in ctx.guild.members:
                if(int(u.id) == UID):
                    member = u
                    break
            for r in ctx.guild.roles:
                if(str(r) == role):
                    print("Adding role: " + str(r))
                    await member.add_roles(r)
                    break
        except Exception as e:
            print(e)
            print("Didnt work")
    else:
        await ctx.send("Okay sweaty :^)")

@bot.command()
async def goon(ctx, UID:int):
    if(ctx.author.id == 380801506137473034 or ctx.author.id == 103702122251436032 or ctx.author.id == 458425335227088936):
        try:
            for u in ctx.guild.members:
                if(int(u.id) == UID):
                    member = u
                    break
            i = 15

            while(i>0):
                await member.edit(mute=True)
                time.sleep(0.25)
                await member.edit(mute=False)
                time.sleep(0.25)
                i -= 1
        except:
            print("Didnt work")
    else:
        await ctx.send("God.....")
@bot.command()
async def spinCycle(ctx, UID:int):
    if(ctx.author.id == 380801506137473034 or ctx.author.id == 103702122251436032 or ctx.author.id == 458425335227088936):
        try:
            member = None
            for u in ctx.guild.members:
                if(int(u.id) == UID):
                    member = u
                    break
            channels = []
            for channel in ctx.message.guild.voice_channels:
                channels.append(channel)
            random.shuffle(channels)
            for channel in channels:
                await member.edit(voice_channel=channel)
                time.sleep(0.25)
            channels.reverse()
            for channel in channels:
                await member.edit(voice_channel=channel)
                time.sleep(0.25)
        except Exception as e:
            print(e)
            print("Didnt work")
    else:
        await ctx.send("Okay retard... You wanted the funny...")
        member = None
        for u in ctx.guild.members:
            if(int(u.id) == ctx.message.author.id):
                member = u
                break
        channels = []
        for channel in ctx.message.guild.voice_channels:
            channels.append(channel)
        random.shuffle(channels)
        for channel in channels:
            await member.edit(voice_channel=channel)
            time.sleep(0.25)
        channels.reverse()
        for channel in channels:
            await member.edit(voice_channel=channel)
            time.sleep(0.25)

@bot.command()
async def clown(ctx):
    if(ctx.author.id == 380801506137473034 or ctx.author.id == 103702122251436032):
        try:
            members = []
            for channel in ctx.guild.voice_channels:
                for member in channel.members:
                    members.append(member)
            channels = []
            for channel in ctx.message.guild.voice_channels:
                channels.append(channel)

            randomChannels = channels

            for member in members:
                random.shuffle(channels)
                randomChannels = channels
                for channel in randomChannels:
                    await member.edit(voice_channel=channel)
                    time.sleep(0.15)
            randomChannel = random.choice(channels)
            for member in members:
                await member.edit(voice_channel=randomChannel)
            await ctx.send("You've all been clowned! Have a good day in " + randomChannel)


        except Exception as e:
            print(e)
            print("Didnt work")
    else:
        await ctx.send("Fucking clown")
        await ctx.send("Imagine being you rn")
@bot.command()
async def simp(ctx, CID:int, MID:int):
    if(ctx.author.id == 380801506137473034):
        try:
            for channel in ctx.guild.channels:
                if (channel.id == CID):
                    msg = await channel.fetch_message(MID)
                    await msg.delete()
                    break
            
        except Exception as e:
            print(e)
    else:
        await ctx.send("You literal simp oh my god shut up shut the hell up retard")
@bot.command()
async def seethe(ctx, CID:int, UID:int):
    if(ctx.author.id == 380801506137473034):
        try:
            member = None
            for u in ctx.guild.members:
                if(int(u.id) == UID):
                    member = u
                    break
            for channel in ctx.guild.channels:
                if(channel.id == CID):
                    await channel.set_permissions(member, send_messages=True)
        except Exception as e:
            print (e)
    else:
        await ctx.send("Cope")