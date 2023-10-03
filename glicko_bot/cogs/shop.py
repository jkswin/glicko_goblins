"""
Initialise the shop! Users can spend gold to purchase items.
"""


import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import json
import os
import seaborn as sns
import matplotlib.pyplot as plt
from ..modules import user_funcs, server_funcs, art_funcs

sns.set_theme()


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.SHOP_PATH = "glicko_bot/data/art/"

    @commands.command()
    @commands.guild_only()
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
        
        stock = await art_funcs.list_stock()
        for item in stock:
            inv_str = f"Price: {item['base_price']} GLD"
            embed.add_field(name=f"_{item['name']} (UID: {item['uid']})_", value=inv_str, inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["art", "preview", "ap"])
    @commands.guild_only()
    async def art_preview(self, ctx, 
                      uid: int = commands.parameter(description="The unique id of the art.", default=0),
                      ):
        """
        Preview an item from !stock.

        Example usage:
        !preview 2
        """
        item = await art_funcs.get_art(uid)
        if item is None:
            await ctx.send(f"Item No. {uid} doesn't exist or isn't for sale.")
            return
        
        image_path = self.SHOP_PATH + item["path"]
        try: 
            with open(image_path, "rb") as f:
                file = discord.File(f, image_path)
        except FileNotFoundError:
            await ctx.send("I can't seem to find this piece...")
            return 
        
        await ctx.send(f"This is {item['name']}, available for the low price of only {item['base_price']} GLD.\nType _!buy {item['uid']}_ to buy it.", file=file)
        return
            
    
    @commands.command(aliases=["purchase"])
    @commands.guild_only()
    async def buy(self, ctx, 
                      uid: int = commands.parameter(description="The unique id of the art.", default=0),
                      ):
        """
        Purchase an item from !stock using its Unique ID.

        Example usage:
        !buy 1
        """

        item = await art_funcs.get_art(uid, for_sale=True)
        if item is None:
            await ctx.send("I can't find that item in my stock?")
            return 
        
        owner = item.get("owner", None)
        name = item.get("name", "")
        price = item.get('base_price', 0)

        wallet = await user_funcs.get_user_wallet(ctx.author)
        funds = wallet.get("GLD", 0)

        if funds < price:
            await ctx.send(f"You don't have enough GLD to buy {name} for {price} GLD!")
            return
        

        await user_funcs.update_wallet(ctx.author, "GLD", -price)
        if owner is not None:
            owner = discord.utils.get(self.bot.users, name=owner)
            await user_funcs.update_wallet(owner, "GLD", price)

        await art_funcs.change_hands(uid, owner, ctx.author, price)

        await ctx.send(f"@everyone {ctx.message.author.name} bought {name} for {price} GLD.")
            
    
    @commands.guild_only()
    @commands.cooldown(1, 30, BucketType.user)
    @commands.command()
    async def sell(self, ctx, uid: int = commands.parameter(description="The unique id of the art.", default=0), price: float = commands.parameter(description="The price in GLD.", default=1000)):
        """
        Put art up for sale so that !buy can be used to buy it!

        Example usage:
        !sell 3 1700
        """
        tax_pool = await server_funcs.get_tax()
        if price >= tax_pool:
            await ctx.send(f"I think that's a bit unreasonable... Try something less than {tax_pool:,.4f}")
            return 
        
        art = await art_funcs.list_art(ctx.author, uid, price)
        if art is None:
            await ctx.send(f"It doesn't look like you own artwork with that ID.")
            return

        if not art.get("for_sale"):
            await ctx.send(f"{ctx.message.author.name} listed {art['name']} for {price:,} GLD.\n Buy it while you can!")
        else:
            await ctx.send(f"{ctx.message.author.name} re-listed {art['name']} for {price:,} GLD.\nPreviously it was {art.get('base_price'):,}")
    

    @commands.command()
    async def collection(self, ctx, show: int = commands.parameter(description="Whether to display the images or just titles.", default=0)):
        """
        Show off your art collection.
        Add 1 to show the images themselves.

        Example usage:
        !collection
        !collection 0
        !collection 1
        """
        
        title = f"{ctx.author.name}'s collection:"
        await ctx.send(title)
        user_collection = await art_funcs.show_off(ctx.author)
        if bool(show):
            for item in user_collection:
                try:
                    image_path = self.SHOP_PATH + {item["path"]}
                    with open(image_path, "rb") as f:
                        file = discord.File(f, image_path)
                    await ctx.send(f"{item['name']} (UID: {item['uid']})", file=file)
                except FileNotFoundError:
                    await ctx.send(f"{item['name']} couldn't be found.")
        else:
            embed = discord.Embed(title=title, color=0xE65AD8)
            for item in user_collection:
                embed.add_field(name=f"__{item['name']}__", value=f"(UID: {item['uid']})")
            await ctx.send(embed=embed)

async def setup(bot: commands.bot):
        await bot.add_cog(Shop(bot))