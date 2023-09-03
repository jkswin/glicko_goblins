"""
Initialise the shop! Users can spend gold to purchase items.

TODO: It is currently a bad bad system that keeps everything in JSON and loops through the inventory to find things.
    I will move this to an indexed format at some point but as a poc this works for now.
"""


import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import json
import os
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme()


class Shop(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.SHOP_PATH = "glicko_bot/data/art/"
        self.WALLET_PATH = "glicko_bot/data/users.json"
        self.KITTY_PATH = "glicko_bot/data/kitty.json"

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
                inv_str = "\n".join([f"_{item['name']} (UID: {item['uid']})_ - Price: {item['base_price']} GLD" for item in inventory if bool(item["for_sale"])])
                embed.add_field(name=collection, value=inv_str, inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["art", "preview", "ap"])
    async def art_preview(self, ctx, 
                      uid: int = commands.parameter(description="The unique id of the art.", default=0),
                      ):
        """
        Preview an item from !stock.

        Example usage:
        !preview 2
        """
        path = os.path.join(self.SHOP_PATH, "founding_collection/metadata.jsonl")
        with open(path, "r") as f:
            stock = [json.loads(a) for a in f.readlines()]

        for item in stock:
            if bool(item["for_sale"]):
                if item["uid"] == uid:
                    image_path = self.SHOP_PATH + f"founding_collection/{item['path']}"
                    with open(image_path, "rb") as f:
                        file = discord.File(f, image_path)
                    await ctx.send(f"This is {item['name']}, available for the low price of only {item['base_price']} GLD.\nType _!buy {item['uid']}_ to buy it.", file=file)
                    return
            
    
    @commands.command(aliases=["purchase"])
    async def buy(self, ctx, 
                      uid: int = commands.parameter(description="The unique id of the art.", default=0),
                      ):
        """
        Purchase an item from !stock using its Unique ID.

        Example usage:
        !buy 1
        """
        path = os.path.join(self.SHOP_PATH, "founding_collection/metadata.jsonl")
        with open(path, "r") as f:
            stock = [json.loads(a) for a in f.readlines()]
        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)

        user = str(ctx.author.id)

        if user not in users.keys():
            await ctx.send("How can you buy stuff without a wallet?!")
            return
        
        for art in stock:
            if art.get("uid", False) == uid:
                owner = art.get("owner", "")
                for_sale = art.get("for_sale", 0)
                name = art.get("name", "")
                if bool(for_sale):
                    price = art.get('base_price', 0)
                    funds = users[user].get("GLD")
                    if funds < price:
                        await ctx.send(f"You don't have enough GLD to buy {name} for {price} GLD!")
                    else:
                        users[user]["GLD"] -= price
                        if owner != "":
                            owner_id = discord.utils.get(self.bot.users, name=owner).id
                            users[str(owner_id)]["GLD"] += price

                        art["owner"] = ctx.message.author.name
                        art["for_sale"] = 0
                        art["sale_history"].append({"from":owner, "to": ctx.message.author.name, "price": price})

                        await ctx.send(f"@everyone {ctx.message.author.name} bought {name} for {price} GLD.")
                        with open(path, "w") as f:
                            for a in stock:
                                json.dump(a, f) 
                                f.write("\n")

                        with open(self.WALLET_PATH, "w") as f:
                            json.dump(users, f)
                        
                    return
                
                else:
                    await ctx.send(f"This art is already owned by {owner}!")
                    return
                
        await ctx.send(f"I don't seem to have that registered?")
        return
    
    @commands.cooldown(1, 30, BucketType.user)
    @commands.command()
    async def sell(self, ctx, uid: int = commands.parameter(description="The unique id of the art.", default=0), price: float = commands.parameter(description="The price in GLD.", default=1000)):
        """
        Put art up for sale so that !buy can be used to buy it!

        Example usage:
        !sell 3 1700
        """
        path = os.path.join(self.SHOP_PATH, "founding_collection/metadata.jsonl")
        with open(path, "r") as f:
            stock = [json.loads(a) for a in f.readlines()]

        with open(self.KITTY_PATH, "r") as f:
            tax_pool = json.load(f)["tax"]

        if price >= tax_pool:
            await ctx.send(f"I think that's a bit unreasonable... Try something less than {tax_pool:,.4f}")
            return 
        
        for art in stock:
            if art.get("uid", False) == uid:
                owner = art.get("owner", "")
                if owner == ctx.message.author.name:
                    previous_price = art["base_price"]
                    for_sale = art.get("for_sale", 0)
                    art["base_price"] = price
                    art["for_sale"] = 1

                    if not bool(for_sale):
                        await ctx.send(f"{ctx.message.author.name} listed {art['name']} for {price:,} GLD.\n Buy it while you can!")
                    else:
                        await ctx.send(f"{ctx.message.author.name} re-listed {art['name']} for {price:,} GLD.\nPreviously it was {previous_price:,}")
                    
                    with open(path, "w") as f:
                        for a in stock:
                            json.dump(a, f) 
                            f.write("\n")

                else:
                    await ctx.send(f"You don't own {art['name']}")
                    return
    

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
        
        path = os.path.join(self.SHOP_PATH, "founding_collection/metadata.jsonl")
        with open(path, "r") as f:
            stock = [json.loads(a) for a in f.readlines()]

        title = f"{ctx.author.name}'s collection:"
        await ctx.send(title)
        if bool(show):
            for item in stock:
                if item["owner"] == ctx.author.name:
                    image_path = self.SHOP_PATH + f"founding_collection/{item['path']}"
                    with open(image_path, "rb") as f:
                        file = discord.File(f, image_path)
                    await ctx.send(f"{item['name']} (UID: {item['uid']})", file=file)
        else:
            embed = discord.Embed(title=title, color=0xE65AD8)
            for item in stock:
                if item["owner"] == ctx.author.name:
                    embed.add_field(name=f"__{item['name']}__", value=f"(UID: {item['uid']})")
            await ctx.send(embed=embed)

async def setup(bot: commands.bot):
        await bot.add_cog(Shop(bot))