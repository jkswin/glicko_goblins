import discord
from discord.ext import commands, tasks
import logging
from dotenv import dotenv_values
import os

cfg = dotenv_values(".env")


# initialise logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# necessary for command responses
intents = discord.Intents(messages=True, guilds=True, reactions=True, message_content=True, members=True)

# bot goooooo
bot = commands.Bot(command_prefix="!", intents=intents)


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

if __name__ == "__main__":
    bot.run(cfg["DISCORD"], 
            log_handler=handler, 
            log_level=logging.DEBUG
            )
