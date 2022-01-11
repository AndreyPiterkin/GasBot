import discord
from discord.ext import commands, tasks
import asyncio
import requests
from dotenv import load_dotenv
import os
import time
import json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = os.getenv('API_KEY')
URL = "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey="+API_KEY

help_command = commands.DefaultHelpCommand(no_category="Commands")
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), description="GasBot, the premier gwei monitoring discord bot!", help_command=help_command)

global_info_basefee = 0
global_info_blocknumber = 0

@bot.listen()
async def on_ready():
    print("Ready!")
    getBasePrice.start()
    updateCachedUsers.start()

# subscribe: adds the user who subscribes to the DB
@bot.command(brief="This subscribes you to GasBot's gwei notifs", description="When subscribed (and you enable notifs "+ 
                                                                                "using !start <amount>), you will receive " +
                                                                                " notifs if the gas price ever falls low enough")
async def subscribe(ctx):
    with open("subscribed-users.json", 'r+') as db:
        # converts the db file into a json
        jsonifiedDb = json.load(db) 
        inTable = False
        # check if the user is already in the table
        for user in jsonifiedDb["user_table"]:
            if user["id"] == ctx.author.id:
                inTable = True
        # if not, then add them to table, and notify them on Discord, and exit
        if not inTable:
            jsonifiedDb["user_table"].append({"id": ctx.author.id, "started": False, "low": -1})
            await ctx.send("Subscribed!")
            db.seek(0)
            json.dump(jsonifiedDb, db)
            return
        db.close()
        await ctx.send('User {0.author.name} is already subscribed!'.format(ctx))

# updates the database to reflect the user starting the notif system
@bot.command(brief="Starts GasBot's notif system", description="Call !start <lowAmount> to specify " +
                                                                "the point at which you want to receive " +
                                                                "notifs. For example, !start 150 will " +
                                                                "notify the bot to message you if the " +
                                                                "gas price falls below 150.")
async def start(ctx, lowAmount):
    await dbHandler(ctx, True, lowAmount, "Started")

# if the user provides the wrong number of arguments to the start command
@start.error
async def start_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("Please provide the low gwei amount "+ctx.author.mention)

# updates the database to reflect user stopping
@bot.command(brief="Stops GasBot's notif system", description="Halts all notifs to your account, until re-enabled")
async def stop(ctx):
    await dbHandler(ctx)

# updates database records for specific user
async def dbHandler(ctx, started=False, low=-1, toSend="Stopped"):
    with open("subscribed-users.json", 'r+') as db:
        jsonifiedDb = json.load(db)
        for i in range(len(jsonifiedDb["user_table"])):
            if(jsonifiedDb["user_table"][i]["id"] == ctx.author.id):
                jsonifiedDb["user_table"][i]["started"] = started
                jsonifiedDb["user_table"][i]["low"] = low
                await ctx.send(toSend)
        db.seek(0)
        json.dump(jsonifiedDb,db)
        db.truncate()
        db.close()

@tasks.loop(seconds=0.3)
async def getBasePrice():
    res = (requests.get(URL)).json()
    blockNumber = res["result"]["LastBlock"]
    baseFee = res["result"]["suggestBaseFee"]
    global global_info_basefee, global_info_blocknumber
    if global_info_basefee != baseFee or global_info_blocknumber != blockNumber:
        global_info_basefee, global_info_blocknumber = baseFee, blockNumber
        await notifyUsers()
    print('fee: {0}, time: {1}'.format(global_info_basefee, time.time()))
    # shows the business of the network 
    # TODO: figure out how this works, could be useful
    gasUsedRatio = res["result"]["gasUsedRatio"]

# cache users so user's don't have to be fetched from client repeatedly during runtime
cached_users = {}

# for editing the previos message
previous_message = None

# notifies all users in the cache who are flagged as started, if the base fee (in gwei) is lower than what they specified
async def notifyUsers():
    global previous_message
    global global_info_basefee
    global cached_users
    for userInfo in cached_users.copy().values():
        if global_info_basefee <= userInfo[1]:
            if previous_message is not None:
                await previous_message.edit(content=previous_message.content.replace("*",""))
            previous_message = await userInfo[0].send('**----------------------\nBase Price: {price:.2f}**'.format(price=float(global_info_basefee)))

# updates the local cache every 10 seconds, by reading the DB file and adding any users who are flagged as started, and removing
# any users that are flagged as stopped from the cache
@tasks.loop(seconds=10)
async def updateCachedUsers():
    global cached_users
    print(cached_users)
    with open("subscribed-users.json", 'r') as db:
        jsonifiedDb = json.load(db)
        for user in jsonifiedDb["user_table"]:
            if user["started"]:
                if user["id"] not in cached_users.keys():
                    fetchedUser = await bot.fetch_user(user["id"])
                    cached_users[user["id"]] = [fetchedUser, user["low"]]
            else:
                cached_users.pop(user["id"], None)
        db.close()
    
bot.run(TOKEN)