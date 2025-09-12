import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

'''
This variable is a placeholder for now.
Plan to eventually make it so different servers can have their own individual inventories.
Also make it hold "Item" objects. Item objects will have the following instance variables: name, currentCount, lowCount, lowCountThreshold
Variable lowCount is a boolean to make a /lowstock command to see what inventory needs to be resupplied. 
Variable lowCountThreshold will set the maximum number of a supply before lowCount is true.
'''
inventory = []

'''
This function checks if the user has the proper Discord role/permissions for certain commands.
Plan to eventually make it so server owners can customize what roles are allowed instead of just default Owner and Manager.
'''
def checkPerms(ctx):
    role = discord.utils.get(ctx.guild.roles, name = "Owner")
    if role:
        return # figure out later

@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready!")

@bot.event
async def on_member_join(member):
    await member.send(f"Hello! Here is a tutorial on how to use this bot. (link)")
    # Eventually write a document on how to use the bot.

# The next two functions are test functions. Ignore for now. 
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "cat" in message.content.lower():
        await message.channel.send(f"meow {message.author.mention}")

    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}")

'''
Add an item to the inventory list. Need to set a default number for lowCountThreshold
This does not affect the inventory count. This is just to add new items previously not in inventory/storage.
'''
@bot.command()
async def addItem(ctx, *, msg):
    # Check if user has proper roles first.
    if checkPerms():
        return
    return # finish later


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
