"""
Setup a wallet and exchange currencies.
Visualise how currency values have changed over time.
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


class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.WALLET_PATH = "glicko_bot/data/users.json"
        self.EXCHANGE_PATH = "glicko_bot/data/exchange.json"
        self.HISTORY_PATH = "glicko_bot/data/exchange_history.json"
        self.tax = 0.02

    @commands.Cog.listener()
    async def on_member_join(self, member):
        user_id = str(member.id)
        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)
        if user_id not in users:
            users[user_id] = {"GLD": 100,
                   "SRC": 0,
                   "GRC": 0,
                   }
            with open(self.WALLET_PATH, "w") as f:
                json.dump(users, f)

    @commands.command(aliases=["b"])
    async def balance(self, ctx):
        """
        Display your balance of each currency.

        Example usage:
        !balance
        """

        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)
        user = str(ctx.author.id)
        if user in users:
            embed = discord.Embed(title=f"{ctx.author}'s Balance", color=0xcc0000) 
            for currency, amount in users[user].items():
                embed.add_field(name=currency, value=f"{amount:,.2f}", inline=True)
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"You don't have a wallet yet! Try {ctx.prefix}create_wallet")

    @commands.command(aliases=["cw"])
    async def create_wallet(self, ctx):
        """
        If you somehow end up without a wallet, get a new one...

        Example usage:
        !create_wallet
        """

        user_id = str(ctx.author.id)
        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)
        if user_id not in users:
            users[user_id] = {"GLD": 5, "SRC": 0, "GRC": 0}
            with open(self.WALLET_PATH, "w") as f:
                json.dump(users, f)
            await ctx.send("Wallet created successfully!")
        else:
            await ctx.send("You already have a wallet.")

    @commands.command()
    async def steal(self, ctx):
        """
        Try steal gold. Don't get caught...

        Example usage:
        !steal 
        """
        user_id = str(ctx.author.id)
        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)
        if user_id in users:
            success = bool(random.randint(0,1))
            if success:
                amount = random.randint(1,10)
                users[user_id]["GLD"] += amount
                with open(self.WALLET_PATH, "w") as f:
                    json.dump(users, f)
                await ctx.send(f"{ctx.author} stole {amount} GLD from a passerby!")

            else:
                del users[user_id]
                with open(self.WALLET_PATH, "w") as f:
                    json.dump(users, f)
                await ctx.send(f"{ctx.author}'s wallet was stolen")      
            
        else:
            await ctx.send("You don't have a wallet to add money to!")


    @commands.command(aliases=["gg"])
    async def give_gold(self, ctx, 
                        amount: float = commands.parameter(description="The amount of gold to send."), 
                        member: discord.Member = commands.parameter(description="The username of the person to send it to.")):
        """
        Give gold to another player.

        Example usage:
        !give_gold 10 myfriendsusername
        """
        if amount <= 0:
            await ctx.send("Invalid amount.")
            return

        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)

        user = str(ctx.author.id)
        target_user = str(member.id)

        if user in users and target_user in users:
            if users[user]["GLD"] >= amount:
                users[user]["GLD"] -= amount
                users[target_user]["GLD"] += amount
                with open(self.WALLET_PATH, "w") as f:
                    json.dump(users, f)
                await ctx.send(f"Transferred {amount} GLD to {member.mention}")
            else:
                await ctx.send("You don't have enough GLD.")
        else:
            await ctx.send("Invalid users.")

        

    @commands.command(aliases=["ex"])
    async def exchange(self, ctx, 
                       amount: float = commands.parameter(description="The quantity to exchange."), 
                       from_currency: str = commands.parameter(description="The currency to sell."), 
                       to_currency: str = commands.parameter(description="The currency to buy.")):
        """
        Exchange currencies. Tax is paid on all exchanges.

        Example usage:
        !exchange 10 GLD SRC
        """

        def load_exchange_data():
            with open(self.EXCHANGE_PATH, "r") as exchange_file:
                return json.load(exchange_file)

        user_id = str(ctx.author.id)
        exchange_data = load_exchange_data()

        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)

        if from_currency in exchange_data and to_currency in exchange_data:
            from_rate = exchange_data[from_currency]
            to_rate = exchange_data[to_currency]

            if from_currency == to_currency:
                await ctx.send("Cannot exchange between the same currencies.")
            else:
                if user_id in users:
                    from_balance = users[user_id][from_currency]

                    if from_balance >= amount:
                        exchanged_amount = amount * (from_rate/to_rate)
                        users[user_id][from_currency] -= amount 
                        after_vat = exchanged_amount * (1 - self.tax)
                        users[user_id][to_currency] += after_vat

                        with open(self.WALLET_PATH, "w") as f:
                            json.dump(users, f)

                        await ctx.send(f"Successfully exchanged {amount:,} {from_currency} to {after_vat:,.2f} {to_currency} (Tax Paid: {exchanged_amount - after_vat:,.2f} {to_currency}). ")
                    else:
                        await ctx.send(f"You don't have enough {from_currency} to perform this exchange.")
                else:
                    await ctx.send("Invalid or unsupported currency.")
        else:
            await ctx.send("Invalid or unsupported currencies.")


    @commands.command(aliases=["rh", "history"])
    async def rate_history(self, ctx):
        """
        Display a graph of currency values over time.

        Example usage:
        !rate_history
        """
        #TODO: add optional window param to control timeseries groupings 
        df = pd.read_json(self.HISTORY_PATH).T
        plt.figure(figsize=(15, 8))
        sns.lineplot(df)
        plt.ylabel("Value in Gold (GLD)")
        plt.title("Currency Rates")
        plt.xticks(rotation=45)
        
        buf = io.BytesIO()
        plt.savefig(buf)
        buf.seek(0)

        await ctx.send("Here's how the money's been moving recently.", file=discord.File(buf, "graph.png"))

    @commands.command(aliases=["wealthy"])
    async def richest(self, ctx):
        """
        Display the richest people in the server keeping exact funds private.
        """
        return

async def setup(bot: commands.bot):
        await bot.add_cog(Economy(bot))