"""
Setup a wallet and exchange currencies.
Visualise how currency values have changed over time.
"""


import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
import json
import random
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
from config import Auth
import numpy as np
from ..modules.mongo import *
from ..modules import user_funcs, server_funcs, exchange_funcs

sns.set_theme()


class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.coin_config_path = "coin.cfg"
        self.tax_rate = 0.02
        self.channel_name = "general"

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Give a wallet to new members containing 100 GLD.
        """
        await user_funcs.create_user_wallet(member)

    @commands.command(aliases=["b"])
    @commands.guild_only()
    async def balance(self, ctx):
        """
        Display your balance of each currency.

        Example usage:
        !balance
        """
        wallet = await user_funcs.get_user_wallet(ctx.author)

        if wallet:
            # send user's wallet contents 
            embed = discord.Embed(title=f"{ctx.author}'s Balance\n(Values rounded to 4DP)", color=0xcc0000) 
            for currency, amount in wallet.items():
                embed.add_field(name=currency, value=f"{amount:,.4f}", inline=True)
            await ctx.send(embed=embed)

    @commands.cooldown(1,60, BucketType.user)
    @commands.command()
    @commands.guild_only()
    async def steal(self, ctx):
        """
        Try steal gold. Don't get caught...
        60 Second Cooldown

        Example usage:
        !steal 
        """
        def steal_calc(tax, user_gold, size=1):
            upper_bound = np.min((int(tax) - 9, int(user_gold) + 9))
            lower_bound = np.ceil(upper_bound/2)
            probabilities = np.exp(-np.arange(lower_bound, upper_bound+1)/1000)
            probabilities /= probabilities.sum()
            return int(np.random.choice(np.arange(lower_bound,upper_bound+1), size=size, p=probabilities))

        wallet = await user_funcs.get_user_wallet(ctx.author)
        if wallet:
            success = bool(random.randint(0,1))
            tax = await server_funcs.get_tax()
            if success and tax > 10:
                amount = steal_calc(tax, wallet.get("GLD", 0), size=1)
                await server_funcs.update_tax(-amount)
                await user_funcs.update_wallet(ctx.author, "GLD", amount)
                await ctx.send(f"{ctx.author} stole {amount} GLD!")

            else:
                exchange_rates = await exchange_funcs.get_current_rate()
                exchange_rates = exchange_rates.get("currencies")
                gold_in_wallet = self.wallet_to_gold(ctx.author, exchange_rates)
                await server_funcs.update_tax(gold_in_wallet)
                await user_funcs.reset_user_wallet(ctx.author)
                await ctx.send(f"{ctx.author} was arrested!\nTheir dirty money was seized by the state.")            


    @commands.command(aliases=["gg"])
    @commands.guild_only()
    async def give_gold(self, ctx, 
                        amount: float = commands.parameter(description="The amount of gold to send."), 
                        member: discord.Member = commands.parameter(description="The username of the person to send it to.")):
        """
        Give gold to another player.

        Example usage:
        !give_gold 10 myfriendsusername
        """
        if amount <= 0.001:
            await ctx.send("Invalid amount.")
            return
        
        if ctx.author == member:
            await ctx.send("You can't send money to yourself!")
            return

        giver_wallet = await user_funcs.get_user_wallet(ctx.author)
        receiver_wallet = await user_funcs.get_user_wallet(member)

        if giver_wallet and receiver_wallet:
            if giver_wallet.get("GLD", 0) >= amount:
                await user_funcs.update_wallet(ctx.author, "GLD", -amount)
                await user_funcs.update_wallet(member, "GLD", amount)
                await ctx.send(f"Transferred {amount} GLD to {member.mention}")
            else:
                await ctx.send("You don't have enough GLD.")
        else:
            await ctx.send("Invalid users.")  

    @commands.command(aliases=["ex"])
    @commands.guild_only()
    async def exchange(self, ctx, 
                       amount: float = commands.parameter(description="The quantity to exchange."), 
                       from_currency: str = commands.parameter(description="The currency to sell."), 
                       to_currency: str = commands.parameter(description="The currency to buy.")):
        """
        Exchange currencies. Tax is paid on all exchanges.

        Example usage:
        !exchange 10 GLD SRC
        """

        exchange_data = await exchange_funcs.get_current_rate()
        exchange_data = exchange_data.get("currencies")
        if from_currency in exchange_data and to_currency in exchange_data:
            from_rate = exchange_data[from_currency]
            to_rate = exchange_data[to_currency]

            if from_currency == to_currency:
                await ctx.send("Cannot exchange between the same currencies.")
            else:
                wallet = await user_funcs.get_user_wallet(ctx.author)
                from_balance = wallet.get(from_currency, 0)
            
                if from_balance >= amount:
                    exchanged_amount = amount * (from_rate/to_rate)
                    await user_funcs.update_wallet(ctx.author, from_currency, -amount)
                    after_vat = exchanged_amount * (1 - self.tax_rate)
                    await user_funcs.update_wallet(ctx.author, to_currency, after_vat)

                    tax_taken = exchanged_amount - after_vat
                    tax_in_gold = tax_taken * to_rate

                    await user_funcs.exchange_log(ctx.author, to_currency, from_currency, amount, from_rate/to_rate)

                    await server_funcs.update_tax(tax_in_gold)
                    await ctx.send(f"Successfully exchanged **{amount:,} {from_currency}** to **{after_vat:,.4f} {to_currency}**\nat a rate of roughly {from_rate/to_rate:,.4f}\n(Tax Paid: {exchanged_amount - after_vat:,.4f} {to_currency} or {tax_in_gold:,.4f} GLD). ")
                
                else:
                    await ctx.send(f"You don't have enough {from_currency} to perform this exchange.")
        else:
            await ctx.send("Invalid or unsupported currencies.")


    @commands.command(aliases=["er"])
    @commands.guild_only()
    async def exchange_rate(self, ctx):
        """
        Display the current exchange rates!

        Example usage:
        !exchange_rate
        """
        exchange_data = await exchange_funcs.get_current_rate()
        exchange_data = exchange_data.get("currencies")
        if exchange_data:
            embed = discord.Embed(title="Exchange Rates", color=0x00ff00)  # Green
            for c, r in exchange_data.items():
                embed.add_field(name=c, value=f"{r:,.3f},", inline=True)

            await ctx.send(embed=embed)

    @commands.command(aliases=["rh", "history"])
    @commands.guild_only()
    async def rate_history(self, ctx, currency: str = commands.parameter(description="Display only a specified currency", default=""), n_days: int = commands.parameter(description="The number of days to display.", default=7)):
        """
        Display a graph of currency values over time.
        Specify a currency to only see a graph of that currency.

        Example usage:
        !rate_history
        !rate_history GRC
        !rate_history GRC 1
        """

        if n_days > 31:
            await ctx.send("I can only show you the within the last 31 days!")
            return
        elif n_days < 1:
            await ctx.send("That makes no sense...")
            return
        
        data = await exchange_funcs.get_last_n_days(n_days)
        df = pd.DataFrame(data)
        if not df:
            return
        
        df.set_index("timestamp",inplace=True)
        df.drop(["_id"], axis=1, inplace=True)

        if currency in df.columns:
            df = df[[currency]]
        elif currency == "":
            pass
        else:
            await ctx.send("That currency doesn't exist!")
            return
            
        plt.figure(figsize=(15, 8))
        sns.lineplot(df)
        plt.ylabel("Value in Gold (GLD)")
        plt.title("Currency Rates")
        plt.xticks(rotation=45)
        
        buf = io.BytesIO()
        plt.savefig(buf)
        buf.seek(0)

        await ctx.send("Here's how the money's been moving recently.", file=discord.File(buf, "graph.png"))
        plt.close()

    @commands.command(aliases=["wealthy"])
    @commands.guild_only()
    async def richest(self, ctx):
        """
        Display the richest person in the server keeping indentity private.

        Example usage:
        !richest
        """
        max_gold = 0
        wallets = await user_funcs.get_all_wallets()
        exchange_rates = await exchange_funcs.get_current_rate()
        exchange_rates = exchange_rates.get("currencies")
        for wallet in wallets:
            wallet = wallet.get("wallet", {})
            gold = self.wallet_to_gold(wallet, exchange_rates) 
            if gold > max_gold:
                max_gold = gold
        
        await ctx.send(f"The richest member currently has a total worth of {max_gold:,.3f} GLD!")
    
    @commands.command()
    @commands.guild_only()
    async def tax(self, ctx):
        """
        Display how much tax has been collected so far.
        Tax is collected when making exchanges and when sponsored goblins return funds.

        Example usage:
        !tax
        """
        tax = await server_funcs.get_tax()
        await ctx.send(f"Current Tax pool: {tax:,.3f} GLD!")
        

    def wallet_to_gold(self, wallet: dict, exchange_rates: dict) -> float:
        """
        Takes a wallet, converts its contents to GLD and returns the value.
        """
        gold = 0
        for currency, quantity in wallet.items():
            gold += quantity * exchange_rates.get(currency, 0)
        return gold
    

    @commands.command(aliases=["scratch_card", "sc"])
    @commands.guild_only()
    async def scratch(self, ctx):
        """
        Pay 100 GLD to buy a scratch card. Match 4 icons to win GLD!
        1 in 333 players will win the jackpot of 10,000 GLD!
        Expected Return: 99.3 GLD

        Odds:
        0       - 30%
        50      - 43.1%
        150     - 10.9%
        200     - 15.7%
        10,000  - 0.3%

        Example usage:
        !scratch 
        """
        cost = 100
        prize_model = {
            "prizes": [0, 0.5, 1.5, 2, 100],
            "probabilities": [0.3, 0.431, 0.109, 0.157, 0.003],
            "emojis": ["\U0001F60B", "\U0001F976", "\U0001F621", "\U0001F480", "\U0001F47B"],
        }
        

        wallet = await user_funcs.get_user_wallet(ctx.author)
        if wallet:
            if wallet.get("GLD", 0) < cost:
                await ctx.send(f"With that much gold shouldn't you be looking at better ways of earning money...")
                return 
            
            await server_funcs.update_tax(cost)
            await user_funcs.update_wallet(ctx.author, "GLD", -cost)

            tax = await server_funcs.get_tax()

            ####
            outcome = random.choices([0,1,2,3,4], weights=prize_model["probabilities"])[0]
            prize = prize_model["prizes"][outcome]
            prize_emoji = prize_model["emojis"][outcome]
            payout = int(prize * cost)
            
            scratch_card = []
            for i in range(len(prize_model["emojis"])):
                if i != outcome:
                    scratch_card.extend(3*[prize_model["emojis"][i]])

            random.shuffle(scratch_card)
            scratch_card = scratch_card[:12]

            if bool(prize):
                replacements = np.random.choice(range(len(scratch_card)),size=4,replace=False)
                for c in replacements:
                    scratch_card[c] = prize_emoji

            scratch_card = "\n".join([" ".join(scratch_card[i:i+4]) for i in range(0, len(scratch_card), 4)])
            
            if bool(prize):
                if payout > tax:
                    payout = tax - 10
                await user_funcs.update_wallet(ctx.author, "GLD", payout)
                await server_funcs.update_tax(-payout)
                await ctx.send(f"{scratch_card}\n{ctx.author} matched 4 {prize_emoji}s! They won {payout} GLD!")
            else:
                await ctx.send(f"{scratch_card}\nUnlucky... No matches!")
    
async def setup(bot: commands.bot):
        await bot.add_cog(Economy(bot))