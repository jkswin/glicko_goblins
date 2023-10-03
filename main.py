import discord
from discord.ext import commands, tasks
import logging
from config import Auth
import os
from glicko_bot.modules import mongo, user_funcs, server_funcs, pet_funcs, exchange_funcs, art_funcs


# initialise logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# necessary for command responses
intents = discord.Intents(messages=True, guilds=True, reactions=True, message_content=True, members=True)

description = "I'm Gobbo! You can come to me for help with anything and everything!\n\n\
Most commands in Economy let you view and manage your funds. Funds are kept in a wallet.\
You can exchange between currencies and watch as their values fluctuate!\n\n\
Shop commands let you buy from the shop and from one another. What you might ask? Art!\
Members can trade Gold for ownership of precious artwork.\n\n\
Sponsor commands are my favourite; invest your Gold into daily Goblin Tournaments\
and watch as fighters earn for you.\n\nIf you're uncertain, type !help name_of_command :)"

class GobboBot(commands.Bot):
    accepting_sponsors = False

# bot goooooo
bot = GobboBot(command_prefix=Auth.COMMAND_PREFIX, intents=intents, description=description)


@bot.event
async def on_ready():
    for file in os.listdir("glicko_bot/cogs"):
        if file.endswith(".py") and not file.startswith("__"):
            filename = file[:-3]
            try:
                await bot.load_extension(f"glicko_bot.cogs.{filename}")
                print(f"- {filename} ✅ ")
            except Exception as e:
                print(f"- {filename} ❌ ")
                print(e)

    await mongo.DB.connect()
    if not mongo.DB.is_connected:
        raise RuntimeError("Database access denied")

    await user_funcs.create_table()
    await server_funcs.create_table()
    await pet_funcs.create_table()
    await exchange_funcs.create_table()
    await art_funcs.create_table()
    print("Created/modified tables successfully")

    #await bot.guilds ## create_text_channel(channel_name)

if __name__ == "__main__":
    bot.run(Auth.DISCORD_TOKEN, 
            log_handler=handler, 
            log_level=logging.ERROR,
            )
