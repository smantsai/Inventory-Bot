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

class Item:
    def __init__(self, name, amt, lowCount, lowCountThreshold, location):
        self.name = name # String storing the name of the item
        self.amt = amt # Integer storing the current number of this specific item in inventory
        self.lowCount = lowCount # Boolean storing a True/False value depending on if the item needs to be resupplied soon.
        self.lowCountThreshold = lowCountThreshold # Integer storing the maximum number of the item in inventory before lowCount is True.
        # In otherwords, if amt goes under lowCountThreshold, lowCount will turn true
        self.location = location # String storing the location of this item in the storage room.

'''
This variable is a placeholder for now.
The key is the item name, while the value is the object itself.
Plan to eventually make it so different servers can have their own individual inventories.
Also make it hold "Item" objects. Item objects will have the following instance variables: name, amt, lowCount, lowCountThreshold
Variable lowCount is a boolean to make a /lowstock command to see what inventory needs to be resupplied. 
Variable lowCountThreshold will set the maximum number of a supply before lowCount is true. In otherwords, if amt goes under lowCountThreshold, lowCount will turn true
'''
inventory = {}

'''
lowCountItems holds the names (in string form) of all items in inventory where lowCount is True.
It does NOT store the item itself.
The key and value will both be the item name.
'''
lowCountItems = {}

'''
This function checks if the user has the proper Discord role/permissions for certain commands.
Plan to eventually make it so server owners can customize what roles are allowed instead of just default Owner and Manager.
'''
def checkPerms(ctx):
    role = discord.utils.get(ctx.guild.roles, name = "Owner")
    if role:
        return True
    return False

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
Show all the items in inventory with their current count
'''
@bot.command()
async def showInventory(ctx):
    if len(inventory) == 0:
        await ctx.send("The store's inventory is empty!")
        return
    str = ""
    for itemName in inventory:
        str += itemName + f" - {inventory[itemName].amt} left"+ "\n"
    await ctx.send(str)

'''
Add an item to the inventory list. Need to set a default number for lowCountThreshold
This does not affect the inventory count. This is just to add new items previously not in inventory/storage.
'''
@bot.command()
async def addItem(ctx, *, itemName: str):
    # Check if user has proper roles first.
    lowerItemName = itemName.lower()
    if checkPerms(ctx):
        if lowerItemName in inventory: # Item is already in inventory, so don't add it again.
            await ctx.send(f"{itemName} is already an item in inventory.") # can add the "with x number left in storage" later
            return
        else:
            item = Item(lowerItemName, 0, True, 5, None)
            # The line above sets the itemName, the current item count to 0, the lowCount warning to True
            # the default low count threshold is 5 and the location is None until set up
            inventory[lowerItemName] = item
            lowCountItems[lowerItemName] = lowerItemName    # Because the lowCount warning is set to True on default, we have to add it to lowCountItems
            await ctx.send(f"Successfully added {itemName} into inventory.")
    else: # User does not have the proper roles to do this command.
        await ctx.send("You do not have the proper roles (Owner, Manager) to add items into inventory!")

'''
This function completely removes the item from inventory.
Use this function when the item is removed from the menu.
'''
@bot.command()
async def deleteItem(ctx, *, itemName: str):
    lowerItemName = itemName.lower()
    if not checkPerms(ctx):
        await ctx.send("You do not the proper roles (Owner, Manager) to delete f{itemName} from inventory!")
    if lowerItemName in inventory:
        if lowerItemName in lowCountItems: # Delete from lowCountItems as well
            lowCountItems.pop(lowerItemName)
        del inventory[lowerItemName]
        await ctx.send(f"{itemName} has been successfully deleted from inventory.")
    else:
        await ctx.send(f"{itemName} is not an item in inventory. Please ensure you have the proper name and spelling.")

'''
Show all the items with lowStock as True in inventory
'''
@bot.command()
async def lowStock(ctx):
    if len(lowCountItems) == 0:
        await ctx.send("Nothing! All items are properly stocked :)")
    else: # Show the count of the items
        str = ""
        for name in lowCountItems:
            str += name + f" - {inventory[name].amt} left" + "\n"
        await ctx.send(str)

'''
Adds an integer amount to itemName's amt in inventory if valid.
'''
@bot.command()
async def add(ctx, amount: int, *, itemName: str):
    lowerItemName = itemName.lower()
    if lowerItemName in inventory:
        if amount <= 0: # Don't add negative numbers
            await ctx.send("Error: Please make sure the amount you add is a positive number.")
        else:
            inventory[lowerItemName].amt += amount
            # Check if new amount is greater than itemName's threshold and update lowStockItems if necessary.
            if lowerItemName in lowCountItems and inventory[lowerItemName].amt >= inventory[lowerItemName].lowCountThreshold:
                lowCountItems.pop(lowerItemName)
                inventory[lowerItemName].lowCount = False
            await ctx.send(f"Added {amount} {itemName} into inventory, for a new total of {inventory[lowerItemName].amt}")
    else:
        await ctx.send(f"{itemName} is not an item in inventory. Please ensure you have the proper name and spelling.")

'''
Removes an integer amount to itemName's amt in inventory if valid
'''
@bot.command()
async def take(ctx, amount: int, *, itemName: str):
    lowerItemName = itemName.lower()
    if lowerItemName in inventory:
        if amount <= 0: # Don't subtract negative numbers
            await ctx.send("Error: Please make sure the amount you are taking is a positive number.")
        else:
            inventory[lowerItemName].amt -= amount
            if inventory[lowerItemName].amt <= 0:
                await ctx.send(f"Error: Updated to a negative amount of {itemName}. Please recount your store's inventory to ensure numbers are accurate.")
                # Maybe ping necessary roles
            # Check if new amount is greater than itemName's threshold and update lowStockItems if necessary.
            if not(lowerItemName in lowCountItems) and inventory[lowerItemName].amt <= inventory[lowerItemName].lowCountThreshold:
                lowCountItems[lowerItemName] = lowerItemName
                inventory[lowerItemName].lowCount = True
                await ctx.send(f"Warning: {itemName} is now on low stock!")
            await ctx.send(f"Took {amount} {itemName} from inventory. {inventory[lowerItemName].amt} left.")
    else:
        await ctx.send(f"{itemName} is not an item in inventory. Please ensure you have the proper name and spelling.")
    return

'''
Changes itemName's lowCountThreshold in inventory.
'''
@bot.command()
async def changeThreshold(ctx, *, msg):
    return

'''
Changes itemName's location in inventory if itemName is a valid item in inventory.
Otherwise, send an error message.
'''
@bot.command()
async def updateLocation(ctx, *, msg):
    return

'''
Returns the location of itemName, if itemName is in inventory and itemName's location is set up.
Otherwise, send an error message.
'''
@bot.command()
async def find(ctx, *, itemName):
    item = itemName.lower()
    if item in inventory:
        if inventory[item].location == None:
            await ctx.send(f"{itemName}'s location has not been set up.")
        else:
            await ctx.send(f"{itemName} is found in {inventory[item].location}")
    else:
        await ctx.send(f"{itemName} is not an item in storage. Please ensure you have the proper name and spelling.")

'''
This function sends a direct message to the user with a description of all functions.
'''
@bot.command()
async def commands(ctx):
    return





bot.run(token, log_handler=handler, log_level=logging.DEBUG)
