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
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
from dotenv import dotenv_values
import numpy as np
import datetime
from datetime import timedelta

sns.set_theme()
cfg = dotenv_values(".env")


class Economy(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.WALLET_PATH = "glicko_bot/data/users.json"
        self.EXCHANGE_PATH = "glicko_bot/data/exchange.json"
        self.HISTORY_PATH = "glicko_bot/data/exchange_history.json"
        self.KITTY_PATH = "glicko_bot/data/kitty.json"
        self.ART_PATH = "glicko_bot/data/art/founding_collection/metadata.jsonl"
        self.SCRATCH_HISTORY_PATH = "glicko_bot/data/scratch_history.json"
        self.summoners = json.loads(cfg["SUMMONERS"]) #TODO: Make the default wallet load in all currencies from the .env
        self.tax = 0.02
        self.channel_name = "general"

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Give a wallet to new members containing 100 GLD.
        """
        # get unique user id
        user_id = str(member.id)

        # read in current list of users' wallets
        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)
        
        # check so that you can't abuse leave + join to generate money
        if user_id not in users:
            # give them a wallet with all possible currencies at 0
            # and 100 GLD
            users[user_id] = {"GLD": 100}
            for currency in self.summoners:
                currency_name = currency[0]
                users[user_id].update({currency_name:0})

            # save updated wallets
            with open(self.WALLET_PATH, "w") as f:
                json.dump(users, f)

    @commands.command(aliases=["b"])
    async def balance(self, ctx):
        """
        Display your balance of each currency.

        Example usage:
        !balance
        """

        # read in wallets
        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)

        # get the message sender's unique id to match it to their wallet 
        user = str(ctx.author.id)
        if user in users:
            # send user's wallet contents 
            embed = discord.Embed(title=f"{ctx.author}'s Balance\n(Values rounded to 4DP)", color=0xcc0000) 
            for currency, amount in users[user].items():
                embed.add_field(name=currency, value=f"{amount:,.4f}", inline=True)
            await ctx.send(embed=embed)

        else:
            # notify if they don't have a wallet
            await ctx.send(f"You don't have a wallet yet! Try {ctx.prefix}create_wallet")

    @commands.cooldown(1, 300, BucketType.user)
    @commands.command(aliases=["cw"])
    async def create_wallet(self, ctx):
        """
        If you somehow end up without a wallet, get a new one...
        5 Minute Cooldown

        Example usage:
        !create_wallet
        """

        user_id = str(ctx.author.id)
        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)
        if user_id not in users:
            users[user_id] = {"GLD": 0}
            for currency in self.summoners:
                currency_name = currency[0]
                users[user_id].update({currency_name:0})
                
            with open(self.WALLET_PATH, "w") as f:
                json.dump(users, f)
            await ctx.send("Wallet created successfully!")
        else:
            await ctx.send("You already have a wallet.")

    @commands.cooldown(1,60, BucketType.user)
    @commands.command()
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

        user_id = str(ctx.author.id)
        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)
        if user_id in users:
            success = bool(random.randint(0,1))
            with open(self.KITTY_PATH, "r") as f:
                    kitty = json.load(f)
            if success and kitty["tax"] > 10:
                # calculate steal amount
                amount = steal_calc(kitty["tax"], users[user_id]["GLD"], size=1)
                kitty["tax"] -= amount
                users[user_id]["GLD"] += amount
                with open(self.WALLET_PATH, "w") as f:
                    json.dump(users, f)
                await ctx.send(f"{ctx.author} stole {amount} GLD from a passerby!")

            else:
                gold_in_wallet = self.wallet_to_gold(users[str(user_id)])
                del users[user_id]
                with open(self.WALLET_PATH, "w") as f:
                    json.dump(users, f)
                kitty["tax"] += gold_in_wallet

                await ctx.send(f"{ctx.author} was arrested!\nTheir dirty money was seized by the state.")

            with open(self.KITTY_PATH, "w") as f:
                    json.dump(kitty, f)    
            
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
        if amount <= 0.001:
            await ctx.send("Invalid amount.")
            return
        
        user = str(ctx.author.id)
        target_user = str(member.id)

        if user == target_user:
            await ctx.send("You can't send money to yourself!")
            return

        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)

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

    def load_exchange_data(self):
            with open(self.EXCHANGE_PATH, "r") as exchange_file:
                return json.load(exchange_file)    

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

        user_id = str(ctx.author.id)
        exchange_data = self.load_exchange_data()

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

                        tax_taken = exchanged_amount - after_vat
                        tax_in_gold = tax_taken * to_rate

                        with open(self.WALLET_PATH, "w") as f:
                            json.dump(users, f)

                        # add tax to the kitty
                        with open(self.KITTY_PATH, "r") as f:
                            kitty = json.load(f)

                        kitty["tax"] += tax_in_gold

                        with open(self.KITTY_PATH, "w") as f:
                            json.dump(kitty, f)

                        await ctx.send(f"Successfully exchanged **{amount:,} {from_currency}** to **{after_vat:,.4f} {to_currency}**\nat a rate of roughly {from_rate/to_rate:,.4f}\n(Tax Paid: {exchanged_amount - after_vat:,.4f} {to_currency} or {tax_in_gold:,.4f} GLD). ")
                    else:
                        await ctx.send(f"You don't have enough {from_currency} to perform this exchange.")
                else:
                    await ctx.send("Invalid or unsupported currency.")
        else:
            await ctx.send("Invalid or unsupported currencies.")

    @commands.command(aliases=["er"])
    async def exchange_rate(self, ctx):
        """
        Display the current exchange rates!

        Example usage:
        !exchange_rate
        """
        exchange_data = self.load_exchange_data()
        message = f"The current exchange rates are:"
        embed = discord.Embed(title="Hourly Rate Update", color=0x00ff00, description=message)  # Green
        for c, r in exchange_data.items():
            embed.add_field(name=c, value=f"{r:,.3f},", inline=True)

        await ctx.send(embed=embed)

    @commands.command(aliases=["rh", "history"])
    async def rate_history(self, ctx, currency: str = commands.parameter(description="Display only a specified currency", default=""), n_days: int = commands.parameter(description="The number of days to display.", default=7)):
        """
        Display a graph of currency values over time.
        Specify a currency to only see a graph of that currency.

        Example usage:
        !rate_history
        !rate_history GRC
        !rate_history GRC 1
        """

        if n_days > 7:
            await ctx.send("I can only show you the within the last 7 days!")
            return
        elif n_days < 1:
            await ctx.send("That makes no sense...")
            return
        
        df = pd.read_json(self.HISTORY_PATH).T
        today = datetime.datetime.today()
        ago = today - datetime.timedelta(days=n_days)
        df = df.loc[df.index > ago]

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
    async def richest(self, ctx):
        """
        Display the richest person in the server keeping indentity private.

        Example usage:
        !richest
        """
        max_gold = 0
        with open(self.WALLET_PATH, "r") as f:
            wallets = json.load(f)
        for user, wallet in wallets.items():
            gold = self.wallet_to_gold(wallet)
            
            if gold > max_gold:
                max_gold = gold
        
        await ctx.send(f"The richest member currently has a total worth of {max_gold:,.3f} GLD!")
    
    @commands.command()
    async def tax(self, ctx):
        """
        Display how much tax has been collected so far.
        Tax is collected when making exchanges and when sponsored goblins return funds.

        Example usage:
        !tax
        """
        with open(self.KITTY_PATH, "r") as f:
            kitty = json.load(f)
        await ctx.send(f"Current Tax pool: {kitty['tax']:,.3f} GLD!")
        

    def wallet_to_gold(self, wallet: json) -> float:
        """
        Takes a wallet, converts its contents to GLD and returns the value.
        """
        exchange_rates = self.load_exchange_data()
        gold = 0
        for currency, quantity in wallet.items():
            gold += quantity * exchange_rates.get(currency, 0)
        return gold
    

    @commands.command(aliases=["scratch_card", "sc"])
    async def scratch(self, ctx):
        """
        Pay 100 GLD to buy a scratch card. Match 4 icons to win GLD!
        1 in 333 players will win the jackpot of 10,000 GLD!

        Odds:
        0       - 30%
        50      - 42%
        150     - 15%
        200     - 12.7%
        10,000  - 0.3%

        Example usage:
        !scratch 
        """
        cost = 100
        prize_model = {
            "prizes": [0, 0.5, 1.5, 2, 100],
            "probabilities": [0.3, 0.42, 0.15, 0.127, 0.003],
            "emojis": ["\U0001F60B", "\U0001F976", "\U0001F621", "\U0001F480", "\U0001F47B"],
        }
        

        user_id = str(ctx.author.id)

        with open(self.WALLET_PATH, "r") as f:
            users = json.load(f)

        if user_id in users:
            if users[user_id]["GLD"] < cost:
                await ctx.send(f"With that much gold shouldn't you be looking at better ways of earning money...")
                return 
            
            with open(self.KITTY_PATH, "r") as f:
                kitty = json.load(f)

            users[user_id]["GLD"] -= cost
            ####
            outcome = random.choices([0,1,2,3,4], weights=prize_model["probabilities"])[0]
            prize = prize_model["prizes"][outcome]
            prize_emoji = prize_model["emojis"][outcome]

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
                payout = int(prize * cost)
                if payout > kitty["tax"] + 10:
                    payout = kitty["tax"] - 10
                users[user_id]["GLD"] += payout
                kitty["tax"] -= payout
                await ctx.send(f"{scratch_card}\n{ctx.author} matched 4 {prize_emoji}s! They won {payout} GLD!")
                ####
            else:
                await ctx.send(f"{scratch_card}\nUnlucky... No matches!")

            with open(self.WALLET_PATH, "w") as f:
                json.dump(users, f)

            with open(self.KITTY_PATH, "w") as f:
                    json.dump(kitty, f)

            with open(self.SCRATCH_HISTORY_PATH, "a") as f:
                str_time = datetime.datetime.now().strftime("%m_%d_%Y__%H_%M_%S")
                json.dump({"username": ctx.author, "user_id": user_id, "time":str_time, "payout": payout, "cost": cost}, f)
                f.write("\n")
            
        else:
            await ctx.send("You don't have a wallet!")
    
async def setup(bot: commands.bot):
        await bot.add_cog(Economy(bot))