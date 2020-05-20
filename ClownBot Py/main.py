import discord
import random
import json
from discord.ext import tasks, commands
from pymongo import MongoClient
import time
import asyncio

with open("config.json") as f:
    configData = json.load(f)
with open("chatlog.json") as g:
    chatData = json.load(g)


prefix = configData["information"][0]["prefix"]
dtoken = configData["tokens"][0]["token"]
mongoPath = configData["tokens"][0]["mongoPath"]

client = MongoClient(mongoPath)

# database clients
dbDiscord = client["Discord"]
dbFirstBankOfFunny = client["FirstBankOfFunny"]

description = (
    """Clowbot commands and such. Ping Memely if you need any help"""
)
bot = commands.Bot(command_prefix=prefix, description=description)

# defaults
defaultFunnyCreditScore = 500
defaultFunnyTransactions = 5
defaultFunnyWage = 11


@bot.command()
async def resetFunny(ctx):
    if ctx.author.id == 380801506137473034:
        try:
            serverID = ctx.guild.id
            queueUp = dbFirstBankOfFunny[str(serverID)]
            inDb = queueUp.find()

            for entry in inDb:
                entryBalance = entry["Balance"]
                resetBal = entryBalance * -1
                print(entry["User"])
                print(entryBalance)
                print(resetBal)
                account = getAccount(entry["User ID"], serverID)
                try:
                    updateBalance(serverID, account, resetBal, False)
                    account = getAccount(entry["User ID"], serverID)
                    updateBalance(serverID, account, 100, False)
                except Exception:
                    print("Failed updateBalance")

                account = getAccount(entry["User ID"], serverID)
                entryWorked = account["Funny Worked"]
                resetWorked = entryWorked + (entryWorked * -1)
                try:
                    updateFunnyWorked(serverID, account, resetWorked)
                except Exception:
                    print("Failed update Funny Worked")
        except Exception:
            print("Failed")
    else:
        await ctx.send("Cringe-ass")


@tasks.loop(hours=6)
async def transReset():
    for guild in bot.guilds:
        for member in guild.members:
            if checkIfAccountExists(member.id, guild.id):
                account = getAccount(member.id, guild.id)
                try:
                    updateTransactions(guild.id, account)
                except Exception as e:
                    print(
                        "Unable to update trans for "
                        + str(member)
                        + ". Reason:\n"
                        + e
                    )
        print("--------------------------")


@tasks.loop(hours=12)
async def payday():

    for guild in bot.guilds:
        print("--------------------------")
        print("Paycheck Summary: " + str(guild))

        for member in guild.members:
            if checkIfAccountExists(member.id, guild.id):
                account = getAccount(member.id, guild.id)
                wage = account["Funny Wage"]
                worked = account["Funny Worked"]
                paycheck = account["Funny Wage"] * account["Funny Worked"]

                print("    ###########################")
                print("          User: " + str(member))
                print("    Funny Wage: " + str(wage))
                print("    Funny Wage: " + str(worked))
                print("      Paycheck: " + str(paycheck))

                try:
                    updateBalance(guild.id, account, paycheck, False)
                    updateFunnyWorked(
                        guild.id, account, account["Funny Worked"] * -1
                    )
                    # updateTransactions(guild.id, account)
                    print(
                        "    Updated "
                        + str(member)
                        + "'s balance with a funny paycheck of "
                        + str(paycheck)
                    )
                    print("    ###########################")
                except Exception:
                    print(
                        "Unable to update "
                        + str(member)
                        + "'s paycheck of "
                        + str(paycheck)
                    )
        print("--------------------------")


@bot.event
async def on_ready():
    print("Logged in as")
    print(bot.user.name)
    print(bot.user.id)
    print("------")
    payday.start()
    transReset.start()


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

    serverEmojis = []

    for emoji in message.guild.emojis:
        serverEmojis.append(emoji)

    random.shuffle(serverEmojis)

    # if(userID == 288096609542340610): #Wrong White
    # if(userID == 380801506137473034): #Memely
    # if(userID == 472076407187570688): #Rarity Rover
    # if(userID == 103702122251436032): #Sto
    # if(userID == 213829514818486272): #Ashy
    if userID == 148209473373208577:  # Phanact
        clown = message.channel
        if message.attachments:
            await clown.send(message.attachments[0].url)
        elif "http" in content or "www." in content:
            await clown.send(content)
        else:
            await clown.send("`" + content + "`")
        await clown.send(str(serverEmojis[0]))

    posts = dbDiscord[ID]

    post_data = {
        "content": content,
        "User": user,
        "Channel": channel,
        "Message URL": messageURL,
        "message ID": messageID,
        "User ID": userID,
    }
    try:
        _ = posts.insert_one(post_data)
    except Exception as e:
        print("Did not post to DB successfully. Reason:\n" + e)

    await bot.process_commands(message)

    """async for messages in message.channel.history():
        print(messages.content)"""


@bot.event
async def on_raw_reaction_add(RawReactionEvent):
    message = (
        await bot.get_guild(RawReactionEvent.guild_id)
        .get_channel(RawReactionEvent.channel_id)
        .fetch_message(RawReactionEvent.message_id)
    )
    messageAuthorID = message.author.id

    guildID = RawReactionEvent.guild_id
    reactorUserID = RawReactionEvent.user_id
    emojiName = RawReactionEvent.emoji.name

    print("----------------Reaction Added----------------")
    print("Message Author: " + str(message.author))
    print("Message Author ID: " + str(messageAuthorID))
    print("Server: " + str(guildID))
    print("User:   " + str(reactorUserID))
    print("Reaction: " + emojiName)

    if messageAuthorID == reactorUserID:
        print("Not updating funny worked for self reactions")
        print("----------------------------------------------")
    else:
        if checkIfAccountExists(messageAuthorID, guildID):
            print("Funny Account Found")
            try:
                account = getAccount(messageAuthorID, guildID)
                checkIfAccountHasAllFields(guildID, account)
                updateFunnyWorked(guildID, account, 1)
                print("----------------------------------------------")
                print("Successfully updated Funny Worked")
                print("----------------------------------------------")
            except Exception as e:
                print("Failed to update funny worked!")
                print("----------------------------------------------")
                print(e)
        else:
            print("No funny account found")
            print("----------------------------------------------")


@bot.event
async def on_raw_reaction_remove(RawReactionEvent):
    message = (
        await bot.get_guild(RawReactionEvent.guild_id)
        .get_channel(RawReactionEvent.channel_id)
        .fetch_message(RawReactionEvent.message_id)
    )
    messageAuthorID = message.author.id

    guildID = RawReactionEvent.guild_id
    reactorUserID = RawReactionEvent.user_id
    emojiName = RawReactionEvent.emoji.name

    print("----------------Reaction Removed----------------")
    print("Message Author: " + str(message.author))
    print("Message Author ID: " + str(messageAuthorID))
    print("Server: " + str(guildID))
    print("User:   " + str(reactorUserID))
    print("Reaction: " + emojiName)

    if messageAuthorID == reactorUserID:
        print("Not updating funny worked for self reactions")
        print("----------------------------------------------")
    else:
        if checkIfAccountExists(messageAuthorID, guildID):
            print("Funny Account Found")
            try:
                account = getAccount(messageAuthorID, guildID)
                checkIfAccountHasAllFields(guildID, account)
                updateFunnyWorked(guildID, account, -1)
                print("----------------------------------------------")
                print("Successfully updated Funny Worked")
                print("----------------------------------------------")
            except Exception as e:
                print("Failed to update funny worked!")
                print("----------------------------------------------")
                print(e)
        else:
            print("No funny account found")
            print("----------------------------------------------")


@bot.command()
async def commandHelp(ctx):

    embed = discord.Embed(title="Command Help")
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments"
        + "/387432001180925953/591601803033051136/hcc-avatar.png"
    )

    embed.add_field(
        name="!getShare",
        value="Posts a link to a voice chat you are in"
        + " for screen sharing and webcam calls",
        inline=False,
    )
    embed.add_field(
        name="!requestBanner <image link> <name (one word)>",
        value="Sends banners off to a queue for admins"
        + " to double check before putting them into an approved queue",
        inline=False,
    )
    embed.add_field(
        name="!displayBannerQueue",
        value="Displays both the request banner"
        + " queue and the mod approved queue",
        inline=False,
    )
    embed.add_field(
        name="!commandHelp",
        value="Displays help dialogues for ClownBot commands",
        inline=False,
    )

    await ctx.send(embed=embed)


@bot.command()
async def getShare(ctx):
    """Posts a link to a voice chat you
    are in for screen sharing and webcam calls"""
    if ctx.message.author.voice.channel is not None:
        voiceChannelName = str(
            ctx.guild.get_channel(ctx.message.author.voice.channel.id)
        )
        voiceChannelID = str(ctx.message.author.voice.channel.id)
        serverID = str(ctx.guild.id)
        commanderName = str(ctx.message.author)

        embed = discord.Embed(
            title="Voice call screenshare and camera link for "
            + voiceChannelName,
            color=0x97A7D2,
        )
        embed.set_author(name=commanderName)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments"
            + "/229820513738948609/590028508147744798/sig-4036785.png"
        )
        embed.add_field(
            name="Current Voice Chat: " + voiceChannelName,
            value="Voice Chat ID: " + voiceChannelID,
            inline=False,
        )
        embed.add_field(
            name="Video Call Link",
            value="["
            + voiceChannelName
            + "](http://www.discordapp.com/channels/"
            + serverID
            + "/"
            + voiceChannelID
            + ")",
            inline=False,
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("You aren't in a voice chat, clown")


@bot.command()
async def funny(ctx, UID: int, role: str):
    if ctx.author.id == 380801506137473034:
        try:
            member = ctx.guild.get_member(UID)
            if role in [str(x) for x in member.roles]:
                print("Removing role: " + role)
                await member.remove_roles(role)
        except Exception as e:
            print(e)
            print("Didnt work")
    else:
        await ctx.send("You're not funny enough")


@bot.command()
async def unfunny(ctx, UID: int, role: str):
    if ctx.author.id == 380801506137473034:
        try:
            member = ctx.guild.get_member(UID)
            if role in [str(x) for x in ctx.guild.roles]:
                await member.add_roles(role)
        except Exception as e:
            print(e)
            print("Didnt work")
    else:
        await ctx.send("Okay sweaty :^)")


@bot.command()
async def goon(ctx, UID: int):
    if ctx.author.id in [
        380801506137473034,
        103702122251436032,
        458425335227088936,
    ]:
        try:
            member = ctx.guild.get_member(UID)
            for i in range(10, 0, -1):
                await member.edit(mute=True)
                await asyncio.sleep(0.25)
                await member.edit(mute=False)
                await asyncio.sleep(0.25)
        except Exception:
            print("Didn't work")
    else:
        await ctx.send("God.....")


@bot.command()
async def shutTheFuckUp(ctx, UID: int):
    if ctx.author.id in [
        380801506137473034,
        103702122251436032,
        458425335227088936,
    ]:
        try:
            member = ctx.guild.get_member(UID)
            await member.edit(mute=True)
        except Exception as e:
            print("Didnt work. Reason:\n" + e)
    else:
        await ctx.send("God.....")


@bot.command()
async def wakeTheFuckUp(ctx, UID: int):
    if ctx.author.id in [
        380801506137473034,
        103702122251436032,
        458425335227088936,
    ]:
        try:
            member = ctx.guild.get_member(UID)
            await member.edit(mute=False)
        except Exception as e:
            print("Didnt work. Reason:\n" + e)
    else:
        await ctx.send("God.....")


@bot.command(name="spinCycle")
async def spinCycle(ctx, UID: int):
    if ctx.author.id in [
        380801506137473034,
        103702122251436032,
        458425335227088936,
        96799634948640768,
    ]:
        try:
            member = ctx.guild.get_member(UID)
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
        member = ctx.guild.get_member(ctx.message.authod.id)
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


@bot.command(name="voiceTestJoin")
async def voiceTestJoin(ctx, UID: int):
    channel = ctx.author.voice.channel
    await channel.connect()


@bot.command(name="voiceTestLeave")
async def voiceTestLeave(ctx):
    await ctx.voice_client.disconnect()


@bot.command(name="voiceTestPlay")
async def voiceTestPlay(ctx):
    channel = ctx.author.voice.channel
    voice = await channel.connect()
    source = discord.FFmpegPCMAudio(
        executable="C:/ffmpeg/bin/ffmpeg.exe", source="./sound/world.mp3"
    )
    voice.play(source)


@bot.command()
async def clown(ctx):
    if ctx.author.id == 380801506137473034:
        try:
            members = []
            for channel in ctx.guild.voice_channels:
                for member in channel.members:
                    members.append(member)
            channels = []
            for channel in ctx.message.guild.voice_channels:
                channels.append(channel)

            randomChannels = channels

            for channel in randomChannels:
                await member.edit(voice_channel=channel)
                time.sleep(0.15)
            randomChannel = random.choice(channels)
            for member in members:
                await member.edit(voice_channel=randomChannel)
            await ctx.send(
                "You've all been clowned! Have a good day in " + randomChannel
            )

        except Exception as e:
            print(e)
            print("Didnt work")
    else:
        await ctx.send("Fucking clown")
        await ctx.send("Imagine being you rn")


@bot.command()
async def simp(ctx, CID: int, MID: int):
    if ctx.author.id == 380801506137473034:
        try:
            channel = ctx.guild.get_channel(CID)
            msg = await channel.fetch_message(MID)
            await msg.delete()
        except Exception as e:
            print(e)
    else:
        await ctx.send(
            "You literal simp oh my god shut up shut the hell up retard"
        )


@bot.command()
async def seethe(ctx, CID: int, UID: int):
    if ctx.author.id == 380801506137473034:
        try:
            member = ctx.guild.get_member(UID)
            channel = ctx.guild.get_channel(CID)
            await channel.set_permissions(member, send_messages=True)
        except Exception as e:
            print(e)
    else:
        await ctx.send("Faggot")


@bot.command()
async def repeat(ctx, times: int, content: str):
    """Repeats a message multiple times."""
    if ctx.author.id == 380801506137473034:
        if times > 150:
            await ctx.send("Boi you just spamming at that point")
        # elif '@' in content:
        #     await ctx.send('Dont @ me bro')
        else:
            for i in range(times):
                await ctx.send(content)
    else:
        for i in range(times):
            await ctx.send("Sorry, autism detected, please stop")


@bot.command()
async def funnyBankHelp(ctx):
    embed = discord.Embed(title="Funny Bank Menu")
    embed.set_thumbnail(
        url="https://cdn.discordapp.com/attachments"
        + "/629188664626380801/682792732993126433/emote.png"
    )

    embed.add_field(
        name="!createFunnyAccount",
        value="Make a new funny account",
        inline=False,
    )
    embed.add_field(
        name="!balance",
        value="Posts your funny account balance (in funny bucks)",
        inline=False,
    )
    embed.add_field(
        name="!charge <user> <amount>",
        value="Charges user funny bucks",
        inline=False,
    )
    embed.add_field(
        name="!give <user> <amount>",
        value="Gives user funny bucks",
        inline=False,
    )
    embed.add_field(
        name="!funnyLoan [Not implimented yet]",
        value="Take out a funny loan",
        inline=False,
    )

    await ctx.send(embed=embed)


@bot.command()
async def account(ctx):

    ID = str(ctx.message.guild.id)
    userID = ctx.message.author.id
    if not checkIfAccountExists(userID, ID):
        await ctx.send(
            "You do not have a funny account!"
            + " Make one with `!createFunnyAccount`"
            + " to get started with First Bank of Funny today!"
        )
    else:
        account = getAccount(userID, ID)

        embed = discord.Embed(title="Funny Bank Menu")
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments"
            + "/629188664626380801/682792732993126433/emote.png"
        )

        embed.add_field(
            name="User",
            value="Account Holder Name: " + str(account["User"]),
            inline=False,
        )
        embed.add_field(
            name="Balance",
            value="Balance: " + str(account["Balance"]),
            inline=False,
        )
        embed.add_field(
            name="Funny Credit Score",
            value="Funny Credit Score: " + str(account["Funny Credit Score"]),
            inline=False,
        )
        embed.add_field(
            name="Daily Funny Transactions",
            value="Transactions remaining: "
            + str(account["Daily Funny Transactions"]),
            inline=False,
        )
        embed.add_field(
            name="Funny Wage",
            value="Funny Wage: " + str(account["Funny Wage"]),
            inline=False,
        )
        embed.add_field(
            name="Total Funny Worked",
            value="Funny Worked: " + str(account["Funny Worked"]),
            inline=False,
        )

        await ctx.send(embed=embed)


@bot.command()
async def balance(ctx):
    member = ctx.message.author

    ID = str(ctx.message.guild.id)
    userID = ctx.message.author.id
    if not checkIfAccountExists(userID, ID):
        await ctx.send(
            "You do not have a funny account!"
            + " Make one with `!createFunnyAccount`"
            + " to get started with First Bank of Funny today!"
        )
    else:
        account = getAccount(userID, ID)
        await ctx.send(
            member.name
            + ", you currently have "
            + str(account["Balance"])
            + " funny bucks."
        )


@bot.command()
async def thenIllMakeAFriendshipProblem(ctx, member: discord.Member):
    if ctx.author.id == 380801506137473034:

        ID = str(ctx.message.guild.id)

        user = member.name
        userID = member.id

        try:
            if not checkIfAccountExists(userID, ID):
                queueUp = dbFirstBankOfFunny[str(ID)]
                post_data = {
                    "User": user,
                    "User ID": userID,
                    "Balance": 100,
                    "Funny Credit Score": 500,
                    "Daily Funny Transactions": 5,
                    "Funny Wage": 10,
                    "Funny Worked": 0,
                }

                queueUp.insert_one(post_data)
                await ctx.send(
                    "Checking funny credit score for " + member.name + "..."
                )
                time.sleep(3)
                await ctx.send(
                    "Funny credit score is good. Creating account for "
                    + member.name
                    + "! Starting bonus is 100 funny bucks. Have a funny day!"
                )
            else:
                account = getAccount(userID, ID)
                await ctx.send(
                    "You already have a funny account."
                    + " Im taking away 1 funny buck for that......."
                )
                updateBalance(ID, account, -1, False)

        except Exception as e:
            await ctx.send("Something went wrong...")
            await ctx.send(e)
            await ctx.send("Ping Memely till he starts fixing it...")
    else:
        await ctx.send("Cope")


@bot.command()
async def createFunnyAccount(ctx):

    ID = str(ctx.message.guild.id)

    user = ctx.message.author.name
    userID = ctx.message.author.id
    member = ctx.message.author

    try:
        if not checkIfAccountExists(userID, ID):
            queueUp = dbFirstBankOfFunny[str(ID)]
            post_data = {
                "User": user,
                "User ID": userID,
                "Balance": 100,
                "Funny Credit Score": 500,
                "Daily Funny Transactions": 5,
                "Funny Wage": 10,
                "Funny Worked": 0,
            }

            queueUp.insert_one(post_data)
            await ctx.send(
                "Checking funny credit score for " + member.name + "..."
            )
            time.sleep(3)
            await ctx.send(
                "Funny credit score is good. Creating account for "
                + member.name
                + "! Starting bonus is 100 funny bucks. Have a funny day!"
            )
        else:
            account = getAccount(userID, ID)
            await ctx.send(
                "You already have a funny account."
                + " Im taking away 1 funny buck for that......."
            )
            updateBalance(ID, account, -1, False)

    except Exception as e:
        await ctx.send("Something went wrong...")
        await ctx.send(e)
        await ctx.send("Ping Memely till he starts fixing it...")


@bot.command()
async def charge(ctx, member: discord.Member, funnyBucks: str):
    serverID = ctx.guild.id
    userID = ctx.message.author.id
    unfunnyMemberID = member.id
    if int(funnyBucks) == 0 or int(funnyBucks) < 0:
        await ctx.send("Who are you really helping here...?")
    elif int(funnyBucks) > 50:
        await ctx.send(
            "That amount is too high for personal transactions."
            + " Limit for personal transactions is 50 Funny"
        )
    else:
        try:
            if checkIfAccountExists(
                unfunnyMemberID, serverID
            ) and checkIfAccountExists(userID, serverID):

                checkIfAccountHasAllFields(
                    serverID, getAccount(userID, serverID)
                )
                checkIfAccountHasAllFields(
                    serverID, getAccount(unfunnyMemberID, serverID)
                )

                unfunnyAccount = getAccount(unfunnyMemberID, serverID)
                userAccount = getAccount(userID, serverID)

                if userAccount["Daily Funny Transactions"] <= 0:
                    await ctx.send(
                        "You do not have a sufficient amount of daily"
                        + " transactions available to charge for this funny."
                        + " Use `!account` to check that number."
                    )
                else:
                    updateBalance(
                        serverID, unfunnyAccount, int(funnyBucks) * -1, False
                    )
                    updateBalance(
                        serverID, userAccount, int(funnyBucks), True
                    )

                    if int(funnyBucks) > 20:
                        await ctx.send(
                            ctx.message.author.name
                            + " is charging "
                            + str(member.name)
                            + " a whopping "
                            + funnyBucks
                            + " funny bucks for being big cringe."
                        )
                    else:
                        await ctx.send(
                            ctx.message.author.name
                            + " is charging "
                            + str(member.name)
                            + " "
                            + funnyBucks
                            + " funny bucks for that yikes comment."
                        )
            else:
                await ctx.send(
                    "That user does not yet have a First Bank of Funny"
                    + " account. They will need to `!createFunnyAccount`"
                    + " before you can charge them for being unfunny!"
                )
        except Exception as e:
            await ctx.send("Something went wrong...")
            await ctx.send(e)
            await ctx.send("Ping Memely till he starts fixing it...")


@bot.command()
async def give(ctx, member: discord.Member, funnyBucks: str):
    serverID = ctx.guild.id
    userID = ctx.message.author.id
    funnyMemberID = member.id
    if int(funnyBucks) == 0 or int(funnyBucks) < 0:
        await ctx.send("Who are you really helping here...?")
    elif int(funnyBucks) > 50:
        await ctx.send(
            "That amount is too high for personal transactions."
            + " Limit for personal transactions is 50 Funny"
        )
    else:
        try:
            if checkIfAccountExists(
                funnyMemberID, serverID
            ) and checkIfAccountExists(userID, serverID):

                checkIfAccountHasAllFields(
                    serverID, getAccount(userID, serverID)
                )
                checkIfAccountHasAllFields(
                    serverID, getAccount(funnyMemberID, serverID)
                )

                funnyAccount = getAccount(funnyMemberID, serverID)
                userAccount = getAccount(userID, serverID)

                if userAccount["Daily Funny Transactions"] <= 0:
                    await ctx.send(
                        "You do not have a sufficient amount of daily"
                        + " transactions available to charge for this funny."
                        + " Use `!account` to check that number."
                    )
                else:
                    updateBalance(
                        serverID, funnyAccount, int(funnyBucks), False
                    )
                    updateBalance(
                        serverID, userAccount, int(funnyBucks) * -1, True
                    )

                    if int(funnyBucks) > 20:
                        await ctx.send(
                            ctx.message.author.name
                            + " is giving "
                            + str(member.name)
                            + " a whopping "
                            + funnyBucks
                            + " funny bucks for making the whole squad laugh."
                        )
                    else:
                        await ctx.send(
                            ctx.message.author.name
                            + " is giving "
                            + str(member.name)
                            + " "
                            + funnyBucks
                            + " funny for the nose-exhale."
                        )
            else:
                await ctx.send(
                    "That user does not yet have a First Bank of Funny"
                    + " account. They will need to `!createFunnyAccount` "
                    + "before you can reward them for being funny!"
                )
        except Exception as e:
            await ctx.send("Something went wrong...")
            await ctx.send(e)
            await ctx.send("Ping Memely till he starts fixing it...")


def getAccount(userID, serverID):
    queueUp = dbFirstBankOfFunny[str(serverID)]
    inDb = queueUp.find()

    for account in inDb:
        if account["User ID"] == int(userID):
            checkIfAccountHasAllFields(serverID, account)

    queueUp = dbFirstBankOfFunny[str(serverID)]
    inDbAfterCheck = queueUp.find()
    for account in inDbAfterCheck:
        if account["User ID"] == int(userID):
            return account


def checkIfAccountExists(userID, serverID):
    queueUp = dbFirstBankOfFunny[str(serverID)]
    inDb = queueUp.find()
    exists = False
    for entry in inDb:
        if entry["User ID"] == int(userID):
            return True
    return exists


def updateBalance(
    serverID, account, balanceDiff: int, countsAsTransaction: bool
):
    queueUp = dbFirstBankOfFunny[str(serverID)]

    balance = int(account["Balance"])
    trans = int(account["Daily Funny Transactions"])
    query = {"_id": account["_id"]}
    newBalance = {"$set": {"Balance": balance + balanceDiff}}

    if countsAsTransaction:
        newTrans = {"$set": {"Daily Funny Transactions": trans - 1}}
        queueUp.find_one_and_update(query, newTrans)

    queueUp.find_one_and_update(query, newBalance)


def updateTransactions(serverID, account):
    queueUp = dbFirstBankOfFunny[str(serverID)]

    query = {"_id": account["_id"]}
    newTrans = {"$set": {"Daily Funny Transactions": 5}}

    queueUp.find_one_and_update(query, newTrans)


def updateFunnyWorked(serverID, account, funnyWorked: int):
    queueUp = dbFirstBankOfFunny[str(serverID)]

    query = {"_id": account["_id"]}
    worked = int(account["Funny Worked"])
    newWorked = {"$set": {"Funny Worked": worked + funnyWorked}}

    try:
        queueUp.find_one_and_update(query, newWorked)
    except Exception as e:
        print(e)


def checkIfAccountHasAllFields(serverID, account):
    queueUp = dbFirstBankOfFunny[str(serverID)].find(account)
    cursor = dbFirstBankOfFunny[str(serverID)]
    keys = getAccountKeys()
    query = {"_id": account["_id"]}
    for document in queueUp:
        for key in keys:
            if key not in document.keys():
                try:
                    # print("Got to checkIfAccountHasAllFields where"
                    # + " key was not in document.keys(). Key:  " + str(key))
                    newValue = {
                        "$set": {
                            str(key): calcNewDefaultForMissingField(
                                account, keys.index(key)
                            )
                        }
                    }
                    cursor.find_one_and_update(query, newValue)
                except Exception as e:
                    print(e)


# Field Updater Methods
def getAccountKeys():
    return [
        "_id",
        "User",
        "User ID",
        "Balance",
        "Funny Credit Score",
        "Daily Funny Transactions",
        "Funny Wage",
        "Funny Worked",
    ]


def calcNewDefaultForMissingField(account, key):
    # print("Got to calcNewDefaultForMissingField with:" + str(key))
    defaults = {
        0: account["_id"],
        1: account["User"],
        2: account["User ID"],
        3: account["Balance"],
        4: defaultFunnyCreditScore,
        5: defaultFunnyTransactions,
        6: defaultFunnyWage,
        7: 0,
    }
    return defaults[key]


# RUNS BOT #
bot.run(dtoken)
