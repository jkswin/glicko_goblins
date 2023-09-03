import discord
from discord.ext import commands, tasks
import json
import datetime
from glicko_goblins.combat import Tournament
import asyncio
import numpy as np
from ..modules.currency_dependencies import currency_query
from ..modules.time import *
from dotenv import dotenv_values
import pandas as pd
import os
import shutil
import pytz


cfg = dotenv_values(".env")


class Background(commands.Cog):
    """
    Home of all background tasks.
    """
    def __init__(self, bot):
        self.bot = bot
        self.channel_name = "general" # channel to send updates to

        self.update_exchange_rate.start()
        self.init_tournament.start()
        self.backup_data.start()
        self.run_tournament.start()
        self.credit.start()

        self.tournament = None
        self.accepting_sponsors = True
        self.tournament_path = "glicko_goblins/data/tournament.pkl"
        self.exchange_path = "glicko_bot/data/exchange.json"
        self.history_path = "glicko_bot/data/exchange_history.json"
        self.user_path = "glicko_bot/data/users.json"
        self.kitty_path = "glicko_bot/data/kitty.json"
        self.archive_path = "glicko_bot/data/archive/"
        self.summoners = json.loads(cfg["SUMMONERS"])
        self.tax = 0.02

    def cog_unload(self):
        self.update_exchange_rate.cancel()
        self.init_tournament.cancel()
        self.run_tournament.cancel()
        self.backup_data.cancel()
        self.credit.cancel()

    @tasks.loop(time=tourn_times)
    async def run_tournament(self):
        """
        Run a tournament day that has been initialised. 
        """
        def logistic_mapping(x, N, k=0.2):
            return (N/10)  * (1 + 1 / (1 + np.exp(-k *(x - N/2)))) - N/10

        # if there isn't an active tournament saved, return
        try:
            self.tournament = Tournament.from_save(self.tournament_path)
        except FileNotFoundError:
            # if the bot starts at a datetime where Tournament has not been created yet
            return
        
        # run a single 'day' of the tournament and save the outcome.
        # this happens multiple times per real day so it essentially just means run X combats.
        self.tournament.run_day()
        self.tournament.save(self.tournament_path)

        # alert the server that combats have happened
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = "Some tournament results are in!\nType !scout to see how they're doing!\n"
                await channel.send(message)

        # load in the users' wallets
        with open(self.user_path, "r") as f:
            users = json.load(f)

        # load in the tax pot
        with open(self.kitty_path, "r") as f:
            kitty = json.load(f)

        # convert the current tournament state to a dataframe for easy sorting
        tournament_table = pd.DataFrame(self.tournament.fighter_info()).sort_values("mean_outcome", ascending=False)
        # sort the tournament participants by ranking. (ranking by glicko isn't strictly sound, but does the job here)
        rankings = tournament_table["tourn_id"].tolist()

        # prepare the output string and a var for tracking the tax
        output = "\n"
        total_round_tax = 0

        # loop through all the fighters
        for goblin in self.tournament.fighters:
            # if they have a sponsor
            if goblin.manager != None:
                position = rankings.index(goblin.tourn_id)
                # calculate the payout to the user.
                # based on funding, WL ratio, relative position based on ranking, eagerness to fight and number of tournaments today
                n_fighters = len(self.tournament.fighters)
                ranking_factor = logistic_mapping(x=n_fighters - position, N=n_fighters, k=0.2)
                pre_payout = (goblin.funding * goblin.winloss() * ranking_factor)/len(start_time)
                
                # half of it goes to tax pool; calc and update
                payout = int(pre_payout * 0.5)
                tax = pre_payout - payout
                kitty["tax"] += tax
                total_round_tax += tax

                # add the amount earned by their sponsored golbins to the users wallets
                manager_id = str(discord.utils.get(self.bot.users, name=goblin.manager).id)
                if manager_id in users.keys():
                    users[manager_id]["GLD"] += payout
                    goblin.earnings += payout

                    # add each users' returns to the output string
                    output += f"@{goblin.manager} earned **{payout:,.2f} GLD** from **{goblin.name}**'s performance!\n\n"
                
                else:
                    # if a manager no longer has a wallet, put their earnings into the tax pot
                    # add this to message
                    output += f"@{goblin.manager} doesn't have a wallet and so {goblin.name}'s earnings were transferred to the state.\n\n"
                    kitty["tax"] += payout
                    total_round_tax += payout

        # alert of amount added to tax pot
        output += f"\n{total_round_tax:,.2f} GLD was paid to the state in Tournament fairs."

        # save the updated tournament (goblin earnings were added to each goblin)
        self.tournament.save(self.tournament_path)

        # save updated user wallets and tax pot
        with open(self.user_path, "w") as f:
            json.dump(users, f)

        with open(self.kitty_path, "w") as f:
            json.dump(kitty, f)

        # send the message to alert people of their returns
        if output != "\n":
            for guild in self.bot.guilds:
                channel = discord.utils.get(guild.text_channels, name=self.channel_name)
                if channel:
                    await channel.send(output)
                
    @tasks.loop(time=start_time)
    async def init_tournament(self):
        """
        Initialise a tournament. The times in start_time have been chosen 
        carefully as to not cause interference between tournaments.

        Includes a 30 minute pause to allow for scouting.
        """
        # if there is a pre-existing tournament, archive it
        if self.tournament is not None:
            str_time = datetime.datetime.now().strftime("%m_%d_%Y__%H_%M_%S")
            path = self.archive_path + f"archive_tourn_{str_time}.json"
            self.tournament.save_dict(path)

        # initialise a tournament
        self.tournament = Tournament(participants=70,
                                        daily_combats=100,
                                        daily_mortalities=0,
                                        )
        
        # load in the tax pool and increase the amount of base funding goblins have 
        with open(self.kitty_path, "r") as f:
            tax = json.load(f)["tax"]

        for fighter in self.tournament.fighters:
            fighter.funding += int(np.log2(tax))

        # run one tournament day to generate preliminary ratings
        self.tournament.run_day()
        # triple the number of combats to make rounds more interesting than preliminary round
        self.tournament.daily_combats *= 3
        # save the new tournament state
        self.tournament.save(self.tournament_path)

        # announce to server that a new tournament started
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"@everyone **{self.tournament.tournament_name} has started!**\n\nYou have **30 minutes** to choose any sponsorships!\nCall *!scout* to see the contestants, *!fund* to invest your gold and *!goblin goblin_id* to view a goblin's stats!\nThe current results are based on pre-tournament matches. Choose wisely!"
                await channel.send(message)
        
        # bot by default does not allow sponsors; allow for sponsors for 30 minutes
        self.bot.accepting_sponsors = True
        await asyncio.sleep(scout_duration)

        # alert server that they have 30 minutes to sponsor goblins
        # and show times that combats are happening
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"**The sponsor window has now closed!**\nThere will be **{len(tourn_times)//len(start_time)}** rounds.\nEach round will be {self.tournament.daily_combats} battles.\nSponsors will earn some GLD after each combat!"
                await channel.send(message)

        # disallow sponsors after the 30 minute sponsor window
        self.bot.accepting_sponsors = False
        
    @tasks.loop(minutes=exchange_update_interval)
    async def update_exchange_rate(self):
        """
        Logic for updating exchange rates, adjusting user wallets to handle new currencies 
        and recording exchange rate history.
        """
        # load in the current rates and make a copy
        with open(self.exchange_path, "r") as f:
            rates = json.load(f)
            previous_rates = rates.copy()

        # request and update the new currencies
        new_rates = await currency_query(self.summoners)
        new_rates_copy = new_rates.copy()

        # calculate how much of each currency is currently in circulation
        totals = {}
        with open(self.user_path) as f:
            user_wallets = json.load(f)
        for currency_quantities in user_wallets.values():
            for currency, quantity in currency_quantities.items():
                if currency != "GLD" and currency in new_rates.keys():
                    if currency not in totals.keys():
                        totals[currency] = quantity
                    else:
                        totals[currency] += quantity

        # take the log of the totals to adjust the rates based on quantity
        log_totals = {currency: np.log10(1 + quantity) for currency, quantity in totals.items()}
        # and use it to adjust them
        new_rates = {key: np.max((new_rates[key] - log_totals.get(key,0), 0.0001))
                       for key in new_rates.keys()}

        # update the rates. This includes any rates that didn't exist prior to this loop
        rates.update(new_rates)

        # now check if any of the users don't have a wallet slot for new currencies
        with open(self.user_path, "r") as f:
            users = json.load(f)

        # if they don't, add it as an option to their wallet
        for user in users.keys():
            for currency in rates.keys():
                if currency not in users[user].keys():
                    users[user][currency] = 0

        # save the users' wallets
        with open(self.user_path, "w") as f:
            json.dump(users,f)

        # make a record of the update
        str_time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        with open("rate_update.log", "a") as f:
            f.write(f"{str_time}\nNew Rates before circulation adjustment:{new_rates_copy}\nTotal of each currency in server: {totals}\nLogarithm of totals: {log_totals}\nUpdated rates: {new_rates}\n\n\n")
        
        # save the new exchange rates
        with open(self.exchange_path, "w") as f:
            json.dump(rates, f)
        
        # load in and save the timestamped exchange rates to the rate history
        with open(self.history_path, "r") as f:
            history = json.load(f)
            history[str_time] = rates

        with open(self.history_path, "w") as f:
            json.dump(history, f)

        # suppress posting rating updates if there isn't a change of more than 0.5% anywhere
        if all([np.absolute(new_rates[curr] - previous_rates.get(curr, 0)) < previous_rates.get(curr, 0)/200 
                for curr in new_rates.keys()]):
            return

        # otherwise send a server message notifying of updated rates
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"*Note that updates of less than 0.5% are not shown*\nRates as of {str_time}:"
                embed = discord.Embed(title="Rate Update", color=0x00ff00, description=message)  # Green
                for pr, r in zip(previous_rates.items(), rates.items()):
                    if pr[0] != "GLD":
                        embed.add_field(name=pr[0], value=f"{pr[1]:.3f} -> {r[1]:.3f}", inline=True)

                await channel.send(embed=embed)

            else:
                print(f"Channel '{self.channel_name}' not found in '{guild.name}'.")

    @tasks.loop(time=backup_times)
    async def backup_data(self):
        """
        Make a backup of the data directory 
        """
        source_directory = 'glicko_bot/data'
        backup_directory = 'glicko_bot/backup'
        
        # Remove the existing backup directory if it exists
        if os.path.exists(backup_directory):
            shutil.rmtree(backup_directory)
        
        # Create the backup directory
        os.makedirs(backup_directory)
        
        # Loop through the contents of the source directory
        for item in os.listdir(source_directory):
            source_item = os.path.join(source_directory, item)
            backup_item = os.path.join(backup_directory, item)
            
            # If the item is a directory, use shutil.copytree to copy the entire directory
            if os.path.isdir(source_item):
                shutil.copytree(source_item, backup_item)

            # If the item is a file, use shutil.copy2 to copy the file with metadata
            elif os.path.isfile(source_item):
                shutil.copy2(source_item, backup_item)
        
        print("Backup completed.")

    @tasks.loop(time=credit_times)
    async def credit(self):
        """
        Daily wallet top up for users using tax pot. 
        Users without much money get a much larger proportion.
        """

        # read in users' wallets and the tax pot
        with open(self.user_path, "r") as f, open(self.kitty_path, "r") as f2:
            users = json.load(f)
            tax_pool = json.load(f2)
        
        # calculate their current gold worth
        user_golds = {user:self.wallet_to_gold(g) for user, g in users.items()}
        # calculate 0.5% of the tax pool
        total_credit = tax_pool["tax"]//200
        # calculate the total amount of money in circulation
        users_total = sum(user_golds.values())
        # for each user, give them a proportion of the tax based on their relative proportion of all gold in existence.
        payouts = {k:(1-(v/users_total))*total_credit for k,v in user_golds.items()}
        
        # update each user's gold
        for user in payouts:
            users[user]["GLD"] += payouts[user]
        
        # update the tax pool
        tax_pool["tax"] -= total_credit

        # save the updates 
        with open(self.user_path, "w") as f:
            json.dump(users, f)
           
        with open(self.kitty_path, "w") as f:
            json.dump(tax_pool, f)

        # alert the server that everyone has been given credit
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"@everyone Credit has been distributed. Check your wallets!"
                await channel.send(message)

    def load_exchange_data(self):
            """
            Helper function to bypass context manager format.
            """
            with open(self.exchange_path, "r") as exchange_file:
                return json.load(exchange_file)   

    def wallet_to_gold(self, wallet: json) -> float:
        """
        Takes a wallet, converts its contents to GLD and returns the value.
        """
        exchange_rates = self.load_exchange_data()
        gold = 0
        for currency, quantity in wallet.items():
            gold += quantity * exchange_rates.get(currency, 0)
        return gold

    @credit.before_loop
    @init_tournament.before_loop
    @run_tournament.before_loop
    @update_exchange_rate.before_loop
    @backup_data.before_loop
    async def before_background_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.bot):
        await bot.add_cog(Background(bot))