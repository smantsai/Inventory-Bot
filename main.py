import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

gi = os.getenv('SERVER_ID')
GUILD_ID = discord.Object(id = gi)

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
def checkPerms(interaction: discord.Interaction) -> bool:
    role = discord.utils.get(interaction.guild.roles, name="Owner")
    if role in interaction.user.roles:
        return True
    return False

@bot.event
async def on_ready():
    print(f"{bot.user.name} is ready!")

    # The following code is to clear all global and guild commands.
    # print(f'We have logged in as {bot.user}')
    # guilds = [guild.id for guild in bot.guilds]
    # print(f'The {bot.user.name} bot is in {len(guilds)} Guilds.\nThe guilds IDs list: {guilds}')
    # for guildId in guilds:
    #     guild = discord.Object(id=guildId)
    #     print(f'Deleting commands from {guildId}.....')
    #     bot.tree.clear_commands(guild=guild,type=None)
    #     await bot.tree.sync(guild=guild)
    #     print(f'Deleted commands from {guildId}!')
    #     continue
    # print('Deleting global commands.....')
    # bot.tree.clear_commands(guild=None,type=None)
    # await bot.tree.sync(guild=None)
    # print('Deleted global commands!')
    try:
        guild = discord.Object(id = gi)
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} commands to {guild.id}.")
    except Exception as e:
        print(f"Problem syncing commands: {e}")


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

@bot.tree.command(name = "hellooo", description = "Says hello", guild = GUILD_ID)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")

@bot.tree.command(name="tester", description = "checking if permissions working", guild = GUILD_ID )
async def test(interaction: discord.Interaction):
    # await interaction.response.send_message("inside")
    if checkPerms(interaction):
        await interaction.response.send_message("permission granted")
    else:
        await interaction.response.send_message("permission failed.")

''' 
Show all the items in inventory with their current count
'''
@bot.tree.command(name = "show_inventory", description = "Shows a list of all inventory items and their amount in storage", guild = GUILD_ID)
async def showInventory(interaction: discord.Interaction):
    if len(inventory) == 0:
        await interaction.response.send_message("The store's inventory is empty!")
        return
    str = ""
    for itemName in inventory:
        str += itemName + f" - {inventory[itemName].amt} left"+ "\n"
    await interaction.response.send_message(str)

'''
Add an item to the inventory list. Need to set a default number for lowCountThreshold
This does not affect the inventory count. This is just to add new items previously not in inventory/storage.
'''
@bot.tree.command(name = "add_item", description = "Add a new item into inventory.", guild = GUILD_ID)
@app_commands.describe(item_name = "name of the new item to be added")
async def addItem(interaction: discord.Interaction, item_name: str):
    # Check if user has proper roles first.
    lowerItemName = item_name.lower()
    if checkPerms(interaction):
        if lowerItemName in inventory: # Item is already in inventory, so don't add it again.
            await interaction.response.send_message(f"{item_name} is already an item in inventory.") # can add the "with x number left in storage" later
            return
        else:
            item = Item(lowerItemName, 0, True, 5, None)
            # The line above sets the itemName, the current item count to 0, the lowCount warning to True
            # the default low count threshold is 5 and the location is None until set up
            inventory[lowerItemName] = item
            lowCountItems[lowerItemName] = lowerItemName    # Because the lowCount warning is set to True on default, we have to add it to lowCountItems
            await interaction.response.send_message(f"Successfully added {item_name} into inventory.")
    else: # User does not have the proper roles to do this command.
        await interaction.response.send_message("You do not have the proper roles (Owner, Manager) to add items into inventory!")

'''
This function completely removes the item from inventory.
Use this function when the item is removed from the menu.
'''
@bot.tree.command(name="delete_item", description = "Removes an item completely from inventory", guild=GUILD_ID)
@app_commands.describe(item_name = "name of the item to be deleted")
async def deleteItem(interaction: discord.Interaction, item_name: str):
    lowerItemName = item_name.lower()
    if not checkPerms(interaction):
        await interaction.response.send_message("You do not the proper roles (Owner, Manager) to delete f{itemName} from inventory!")
    if lowerItemName in inventory:
        if lowerItemName in lowCountItems: # Delete from lowCountItems as well
            lowCountItems.pop(lowerItemName)
        del inventory[lowerItemName]
        await interaction.response.send_message(f"{item_name} has been successfully deleted from inventory.")
    else:
        await interaction.response.send_message(f"{item_name} is not an item in inventory. Please ensure you have the proper name and spelling.")

'''
Show all the items with lowStock as True in inventory
'''
@bot.tree.command(name = "lowStock", description = "shows all low stock items",guild = GUILD_ID)
async def lowStock(interaction: discord.Interaction):
    if len(lowCountItems) == 0:
        await interaction.response.send_message("Nothing! All items are properly stocked :)")
    else: # Show the count of the items
        str = ""
        for name in lowCountItems:
            str += name + f" - {inventory[name].amt} left" + "\n"
        await interaction.response.send_message(str)

'''
Adds an integer amount to itemName's amt in inventory if valid.
'''
@bot.tree.command(name = "add", description = "adds to an item", guild = GUILD_ID)
@app_commands.describe(amount = "amount of the item added", item_name = "name of the item to be added to")
async def add(interaction: discord.Interaction, amount: int, item_name: str):
    lowerItemName = item_name.lower()
    if lowerItemName in inventory:
        if amount <= 0: # Don't add negative numbers
            await interaction.response.send_message("Error: Please make sure the amount you add is a positive number.")
        else:
            inventory[lowerItemName].amt += amount
            # Check if new amount is greater than itemName's threshold and update lowStockItems if necessary.
            if lowerItemName in lowCountItems and inventory[lowerItemName].amt >= inventory[lowerItemName].lowCountThreshold:
                lowCountItems.pop(lowerItemName)
                inventory[lowerItemName].lowCount = False
            await interaction.response.send_message(f"Added {amount} {item_name} into inventory, for a new total of {inventory[lowerItemName].amt}")
    else:
        await interaction.response.send_message(f"{item_name} is not an item in inventory. Please ensure you have the proper name and spelling.")

'''
Removes an integer amount to itemName's amt in inventory if valid
'''
@bot.tree.command(name = "take", description = "removes a number of items from inventory", guild = GUILD_ID)
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

'''
Changes itemName's lowCountThreshold in inventory.
'''
@bot.command()
async def changeThreshold(ctx, newThres: int, *, itemName: str):
    lowerItemName = itemName.lower()
    if lowerItemName in inventory:
        if newThres < 0:
            await ctx.send("Error: Please make sure the new threshold is greater than 0.")
        else:
            inventory[lowerItemName].lowCountThreshold = newThres
    else:
        await ctx.send(f"{itemName} is not an item in inventory. Please ensure you have the proper name and spelling.")
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
