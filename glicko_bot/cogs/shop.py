"""
Initialise the shop! Users can spend gold to purchase items.
"""


import discord
from discord.ext import commands
import json
import random
import os
import pandas as pd
from datetime import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image
import io

sns.set_theme()


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.SHOP_PATH = "glicko_bot/data/art/"

    @commands.command()
    async def stock(self, ctx):
        """
        Display what is available to buy.

        Example usage:
        !stock
        """
        embed = discord.Embed(title="Shop", 
                              description="Welcome to the shop. Only the finest artwork for sale!\nEverything is one of a kind!\nNO REFUNDS", 
                              color=0x674EA7
                              )
        for collection in os.listdir(self.SHOP_PATH):
            items = os.path.join(self.SHOP_PATH, collection, "metadata.jsonl")
            with open(items, "r") as f:
                inventory = [json.loads(item) for item in f.readlines()]
                inv_str = "\n".join([f"_{item['name']}_ - Price: {item['base_price']} GLD" for item in inventory if len(item["owner"]) == 0])
                embed.add_field(name=collection, value=inv_str, inline=False)

        
        await ctx.send(embed=embed)

    @commands.command(aliases=["art", "preview", "ap"])
    async def art_preview(self, ctx, 
                      uid: int = commands.parameter(description="The unique id of the art.", default=0),
                      name: int = commands.parameter(description="The name of the art.", default=""),
                      ):
        """
        COMING SOON! Preview an item from !stock.

        Example usage:
        !preview 3
        """
        return
    
    @commands.command(aliases=["purchase"])
    async def buy(self, ctx, 
                      uid: int = commands.parameter(description="The unique id of the art.", default=0),
                      name: int = commands.parameter(description="The name of the art.", default=""),
                      ):
        """
        COMING SOON! Purchase an item from !stock.

        Example usage:
        !buy 1 Lemons
        """
        return
 

async def setup(bot: commands.bot):
        await bot.add_cog(Shop(bot))