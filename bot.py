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
    notifyUsers.start()


@bot.command(brief="This subscribes you to GasBot's gwei notifs", description="When subscribed (and you enable notifs "+ 
                                                                                "using !start <amount>), you will receive " +
                                                                                " notifs if the gas price ever falls low enough")
# subscribe: adds the user who subscribes to the DB
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

@bot.command(brief="Starts GasBot's notif system", description="Call !start <lowAmount> to specify " +
                                                                "the point at which you want to receive " +
                                                                "notifs. For example, !start 150 will " +
                                                                "notify the bot to message you if the " +
                                                                "gas price falls below 150.")
async def start(ctx, lowAmount):
    await dbHandler(ctx, True, lowAmount, "Started")

@start.error
async def start_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("Please provide the low gwei amount "+ctx.author.mention)

@bot.command(brief="Stops GasBot's notif system", description="Halts all notifs to your account, until re-enabled")
async def stop(ctx):
    await dbHandler(ctx)

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

@tasks.loop(seconds=0.5)
async def getBasePrice():
    res = (requests.get(URL)).json()
    blockNumber = res["result"]["LastBlock"]
    baseFee = res["result"]["suggestBaseFee"]
    global global_info_basefee, global_info_blocknumber
    global_info_basefee, global_info_blocknumber = baseFee, blockNumber
    # shows the business of the network 
    # TODO: figure out how this works, could be useful
    gasUsedRatio = res["result"]["gasUsedRatio"]

cached_users = {}

@tasks.loop(seconds=3)
async def notifyUsers():
    with open("subscribed-users.json", 'r') as db:
        jsonifiedDb = json.load(db)
        for user in jsonifiedDb["user_table"]:
            if user["started"] and global_info_basefee <= user["low"]:
                if user["id"] not in cached_users:
                    fetchedUser = await bot.fetch_user(user["id"])
                    cached_users[user["id"]] = fetchedUser  
                await cached_users[user["id"]].send('Base Price: {0}, Block Number: {1}'.format(global_info_basefee, global_info_blocknumber))
        db.close()
    
bot.run(TOKEN)