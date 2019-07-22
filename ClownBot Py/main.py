import discord
from discord.ext import commands
from discord.utils import get
import random
import json
from pprint import pprint
from discord import NotFound
import requests
import urllib
from discord import Member
from discord.ext.commands import has_permissions, MissingPermissions
from discord.ext.commands import has_permissions, CheckFailure
import copy
import os
from os import listdir
from derpibooru import Search
from pymongo import MongoClient
import time
from threading import Timer
import threading


with open('config.json') as f:
    configData = json.load(f)
with open('chatlog.json') as g:
    chatData = json.load(g)


prefix = configData["information"][0]["prefix"]
dtoken = configData["tokens"][0]["token"]
mongoPath = configData["tokens"][0]["mongoPath"]

client = MongoClient(mongoPath)

#database clients
dbDiscord = client['Discord']
dbRequestBanner = client['bannerRequestQueues']
dbApprovedBanner = client['bannerApprovedQueues']


description = '''Clowbot commands and such. Ping Memely if you need any help'''
bot = commands.Bot(command_prefix=prefix, description=description)


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
@has_permissions(administrator=True)
async def banner(ctx, bannerimage: str):
    serverID = str(ctx.guild.id)
    requestDirName = f"botQueueAwaiting/{serverID}"
    approvedDirName = f"botQueueApproved/{serverID}"
    bannerDirName = f"bannerCommandFolder/{serverID}"
    
    checkDir(requestDirName, approvedDirName, bannerDirName)

    try:
        img_data = requests.get(bannerimage).content
        with open(str(bannerDirName) + "/bannerImage" + '.jpg', 'wb') as handler:
            handler.write(img_data)
        await ctx.guild.edit(banner=open(str(bannerDirName) + "/bannerImage" + '.jpg', mode='rb').read())
    except Exception:
        await ctx.send("Something went wrong")
@banner.error
async def bannerError(ctx, error):
    if isinstance(error, CheckFailure):
        text = "Honk Honk...! Sorry {}, you do not have permissions to do that, clown!".format(ctx.message.author)
        await ctx.send(text)


@bot.command()
async def bannerQueue(ctx):
    """Displays both the request banner queue and the mod approved queue"""

    serverID = str(ctx.guild.id)
    requestDirName = f"botQueueAwaiting/{serverID}"
    approvedDirName = f"botQueueApproved/{serverID}"

    queueUpRequests = dbRequestBanner[str(serverID)]
    queueUpApproved = dbApprovedBanner[str(serverID)]

    # Pink Name zone
    requestEmbed=discord.Embed(title="Current queue for banners requested by users", color=0x97a7d2)
    requestEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/387432001180925953/591601803033051136/hcc-avatar.png")
    
    inDB = queueUpRequests.find()
    filecount = 0
    try:
        for entry in inDB:
            requestedBy = entry['Requesting User']        
            bannerLink = entry['bannerURL']
            filecount += 1

            requestEmbed.add_field(name="Image #" + str(filecount), value=requestedBy + " - [Image Link](" + bannerLink + ")", inline=False)
    except IndexError:
        requestEmbed.add_field(name="No images in the queue...", value="Not a single goddamn one...", inline=False)
    await ctx.send(embed=requestEmbed)

    

    #  Janny approved
    approvedEmbed=discord.Embed(title="Current queue for banners approved by jannies", color=0x97a7d2)
    approvedEmbed.set_thumbnail(url="https://cdn.discordapp.com/attachments/387432001180925953/591601803033051136/hcc-avatar.png")

    inDB = queueUpApproved.find()
    filecount = 0
    try:
        for entry in inDB:
            requestedBy = entry['Requesting User']        
            bannerLink = entry['bannerURL']
            filecount += 1

            approvedEmbed.add_field(name="Image #" + str(filecount), value=requestedBy + " - [Image Link](" + bannerLink + ")", inline=False)
    except IndexError:
        approvedEmbed.add_field(name="No images in the queue...", value="Not a single goddamn one...", inline=False)
    await ctx.send(embed=approvedEmbed)


@bot.command()
async def requestBanner(ctx, bannerImage: str):
    """Sends banners off to a queue for admins to double check before putting them into an approved queue. Requres a link and a name"""
    #renames items in queue with the right numbers in the db
    try:
        renameQueued(ctx.guild.id)
    except:
        await ctx.send("Unable to fix database")
    
    if bannerImage.startswith('http') and bannerImage.lower().endswith(('.png', '.jpg', '.jpeg')):
        serverID = str(ctx.guild.id)
        filecount = 0

        queueUp = dbRequestBanner[str(serverID)]

        inDB = queueUp.find()



        # counts files
        for entry in inDB:
            #print("Got to for loop")
            filecount += 1
        if filecount > 5:
            #print("Got to more than 5 images")
            await ctx.send("Honk...! There is more than 5 images...! Dont kill Memely's computer...!")
        else:
            #print("Got to else")
            post_data = {
            'Requesting User': ctx.message.author.name,
            'bannerURL': bannerImage,
            'File Number': filecount,
            'User ID': ctx.message.author.id
            }
            try:
                await ctx.send("Attempting to add to banner request queue. . .")
                bannerResult = queueUp.insert_one(post_data)
                await ctx.send("Successfully added banner to request queue!")
            except:
                await ctx.send("Honk honk! Did not post to DB successfully!")
    else:
        await ctx.send("Honk honk! Ya typed it wrong, ya dundy! Try !requestBanner <link>")

@requestBanner.error
async def requestBannerError(ctx, error):
    await ctx.send("Honk honk! Ya typed it wrong, ya dundy! Try !requestBanner <link> and make sure its a png, jpg, or jpeg!")


@bot.command()
@has_permissions(administrator=True)
async def startBannerQueue(ctx):
    #starting banner queue ####################################################################################################
    queueUpApproved = dbApprovedBanner[str(ctx.guild.id)]

    inDB = queueUpApproved.find()
    serverID = ctx.guild.id
    requestDirName = f"botQueueAwaiting/{serverID}"
    approvedDirName = f"botQueueApproved/{serverID}"
    bannerDirName = f"bannerCommandFolder/{serverID}"
    
    checkDir(requestDirName, approvedDirName, bannerDirName)

    # for each entry in the database
        # do banner code to change banner
        # run timer func
    for entry in inDB:
        link = entry['bannerURL']   
        try:
            img_data = requests.get(link).content
            #Dont forget to change this to a different dir once you get it going
            with open(str(approvedDirName) + "/bannerImage" + '.jpg', 'wb') as handler:
                handler.write(img_data)
            await ctx.guild.edit(banner=open(str(approvedDirName) + "/bannerImage" + '.jpg', mode='rb').read())
        except Exception:
            await ctx.send("Something went wrong")
        time.sleep(1)

@bot.command()
@has_permissions(administrator=True)
async def nextBanner(ctx):
    #renames items in queue with the right numbers in the db
    try:
        renameQueued(ctx.guild.id)
    except:
        await ctx.send("Unable to fix database")

    queueUpApproved = dbApprovedBanner[str(ctx.guild.id)]
    inDB = queueUpApproved.find()

    serverID = ctx.guild.id
    requestDirName = f"botQueueAwaiting/{serverID}"
    approvedDirName = f"botQueueApproved/{serverID}"
    bannerDirName = f"bannerCommandFolder/{serverID}"
    
    checkDir(requestDirName, approvedDirName, bannerDirName)



    # for each entry in the database
        # do banner code to change banner
        # run timer func
    for entry in inDB:
        link = entry['bannerURL']   
        try:
            await ctx.send("Putting up next banner...")
            img_data = requests.get(link).content
            #saves image locally for upload to banner for server
            with open(str(approvedDirName) + "/bannerImage" + '.jpg', 'wb') as handler:
                handler.write(img_data)
            await ctx.guild.edit(banner=open(str(approvedDirName) + "/bannerImage" + '.jpg', mode='rb').read())
            await ctx.send("Next banner up by " + entry['Requesting User'])

            #deletes entry
            queueUpApproved.delete_one(entry)
            break
        except Exception:
            await ctx.send("Something went wrong")

@startBannerQueue.error
async def startBannerError(ctx, error):
    if isinstance(error, CheckFailure):
        text = "Honk Honk...! Sorry {}, you do not have permissions to do that, clown!".format(ctx.message.author)
        await ctx.send(text)

@bot.command()
@has_permissions(administrator=True)
async def pauseBannerQueue():
    #pausing banner queue ####################################################################################################
    x = 0
@pauseBannerQueue.error
async def pauseBannerError(ctx, error):
    if isinstance(error, CheckFailure):
        text = "Honk Honk...! Sorry {}, you do not have permissions to do that, clown!".format(ctx.message.author)
        await ctx.send(text)

@bot.command()
@has_permissions(administrator=True)
async def approveBanner(ctx, bannerNumber : int):
    #approving banner

    #renames items in queue with the right numbers in the db
    try:
        renameQueued(ctx.guild.id)
    except:
        await ctx.send("Unable to fix database")

    queueUpRequests = dbRequestBanner[str(ctx.guild.id)]
    queueUpApproved = dbApprovedBanner[str(ctx.guild.id)]

    inRequestDB = queueUpRequests.find()
    inApprovedDB = queueUpApproved.find()

    for entry in inRequestDB:
        if entry["File Number"] == bannerNumber-1:
            try:
                await ctx.send("Attempting to add to banner approved queue...")
                bannerApproved = queueUpApproved.insert_one(entry)
                bannerRequested = queueUpRequests.delete_one(entry)
                await ctx.send("Successfully added banner to approved queue!")
                
            except:
                await ctx.send("Honk honk! Did not post to DB successfully!")            
        else:
            x=0
@approveBanner.error
async def approveBannerError(ctx, error):
    if isinstance(error, CheckFailure):
        text = "Honk Honk...! Sorry {}, you do not have permissions to do that, clown!".format(ctx.message.author)
        await ctx.send(text)
    else:
        await ctx.send("Honk honk, fool...! You typed it wrong, and now I'm goonin'...! Type it like !approveBanner <number of the image in the request queue>")

@bot.command()
@has_permissions(administrator=True)
async def disapproveBanner(ctx, bannerNumber : int):
    #disapproving banners

    #renames items in queue with the right numbers in the db
    try:
        renameQueued(ctx.guild.id)
    except:
        await ctx.send("Unable to fix database")

    queueUpRequests = dbRequestBanner[str(ctx.guild.id)]
    inRequestDB = queueUpRequests.find()

    await ctx.send("Disapproving banner number " + bannerNumber + " from request queue")
    for entry in inRequestDB:
        if entry["File Number"] == bannerNumber-1:
            try:
                await ctx.send("Attempting to remove from queue. . .")
                bannerRequested = queueUpRequests.delete_one(entry)
                await ctx.send("Successfully removed banner from request queue!")
            except:
                await ctx.send("Honk honk! Did not remove from DB successfully!")            
        else:
            await ctx.send("That banner doesnt exist!")
@disapproveBanner.error
async def disapproveBannerError(ctx, error):
    if isinstance(error, CheckFailure):
        text = "Honk Honk...! Sorry {}, you do not have permissions to do that, clown!".format(ctx.message.author)
        await ctx.send(text)

@bot.command()
@has_permissions(administrator=True)
async def skipBanner():
    #skipping banners ####################################################################################################
    x = 0
@skipBanner.error
async def skipBannerError(ctx, error):
    if isinstance(error, CheckFailure):
        text = "Honk Honk...! Sorry {}, you do not have permissions to do that, clown!".format(ctx.message.author)
        await ctx.send(text)

@bot.command()
@has_permissions(administrator=True)
async def clearApproved(ctx):
    #clearing accepted queued banners
    queueUpApproved = dbApprovedBanner[str(ctx.guild.id)]
    inApprovedDB = queueUpApproved.find()

    try:
        for entry in inApprovedDB:
            bannerList = queueUpApproved.delete_one(entry)
        await ctx.send("Successfully cleared approved queue!")
    except:
        await ctx.send("Queue not successfully cleared...")
@clearApproved.error
async def clearAcceptedError(ctx, error):
    if isinstance(error, CheckFailure):
        text = "Honk Honk...! Sorry {}, you do not have permissions to do that, clown!".format(ctx.message.author)
        await ctx.send(text)

@bot.command()
@has_permissions(administrator=True)
async def clearRequested(ctx):
    #clearing requested queued banners
    queueUpRequests = dbRequestBanner[str(ctx.guild.id)]
    inRequestDB = queueUpRequests.find()
    try:
        for entry in inRequestDB:
            bannerList = queueUpRequests.delete_one(entry)
        await ctx.send("Successfully cleared request queue!")
    except:
        await ctx.send("Queue not successfully cleared...")
@clearRequested.error
async def clearRequestError(ctx, error):
    if isinstance(error, CheckFailure):
        text = "Honk Honk...! Sorry {}, you do not have permissions to do that, clown!".format(ctx.message.author)
        await ctx.send(text)

############################################   RANDOM STUFF   ############################################
### Test command for resting the renamedQueue() function  ###
@bot.command()
async def rename(ctx):
    await ctx.send("Trying to fix")
    try:
        renameQueued(ctx.guild.id)
        await ctx.send("Stuff's fixed")
    except:
        await ctx.send("Stuff's still broken")
@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)

@bot.command(description='For when you wanna settle the score some other way')
async def choose(ctx, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))

@bot.command()
async def repeat(ctx, times: int, content: str):
    """Repeats a message multiple times."""
    if times > 5:
        await ctx.send('Boi you just spamming at that point')
    elif '@' in content:
        await ctx.send('Dont @ me bro')
    else:
        for i in range(times):
            await ctx.send(content)

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send('{0.name} joined in {0.joined_at}'.format(member))

def checkDir(requestDirName: str, approvedDirName: str, bannerDirName: str) :
    # Create target Directory if don't exist
    for path in [requestDirName, approvedDirName, bannerDirName] :
        if not os.path.exists(path):
            os.mkdir(path)
            print("Directory " , path ,  " Created ")
        else:    
            print("Directory " , path,  " already exists")

#### This is the weird stuff ###
def renameQueued(serverID):
    queueUpApproved = dbApprovedBanner[str(serverID)]
    inApprovedDB = queueUpApproved.find()

    queueUpRequests = dbRequestBanner[str(serverID)]
    inRequestDB = queueUpRequests.find()

    print()

    number = 0
    for request in inRequestDB:
        oldValue = {'File Number' : request['File Number']}
        newValue = { '$set': { 'File Number': int(number)}}
        queueUpRequests.update_one(oldValue, newValue)
        print("Updating" + oldValue + " with " + newValue)
        number +=1
    number = 0
    for approval in inApprovedDB:
        oldValue = {'File Number' : approval['File Number']}
        newValue = { '$set': { 'File Number': int(number)}}
        queueUpApproved.update_one(oldValue, newValue)
        number +=1

bot.run(dtoken)
