"""
The background workings that affect currency values.
"""


import discord
from discord.ext import commands, tasks
import json
import datetime
from glicko_goblins.combat import Tournament
import asyncio
import numpy as np
from ..modules.currency_dependencies import currency_query
from dotenv import dotenv_values
import pandas as pd
import os
import shutil


cfg = dotenv_values(".env")
utc = datetime.timezone.utc

# when tournaments kick off
start_time = datetime.time(hour=20, minute=45, tzinfo=utc)

# When combats happen
tourn_times = [datetime.time(hour=21, minute=30, tzinfo=utc),
               datetime.time(hour=22, tzinfo=utc),
               datetime.time(hour=22, minute=30, tzinfo=utc), # GMT is 1 hour ahead of this
               datetime.time(hour=23, tzinfo=utc),
               datetime.time(hour=23, minute=30, tzinfo=utc),
               datetime.time(hour=00, tzinfo=utc),
               ]

backup_times = [datetime.time(hour=i, tzinfo=utc) for i in range(24)]



class Background(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.channel_name = "general" # channel to send updates to

        self.update_exchange_rate.start()
        self.init_tournament.start()
        self.backup_data.start()

        self.tournament = None
        self.accepting_sponsors = True
        self.tournament_path = "glicko_goblins/data/tournament.pkl"
        self.exchange_path = "glicko_bot/data/exchange.json"
        self.history_path = "glicko_bot/data/exchange_history.json"
        self.user_path = "glicko_bot/data/users.json"
        self.kitty_path = "glicko_bot/data/kitty.json"
        self.summoners = json.loads(cfg["SUMMONERS"])
        self.tax = 0.02

    def cog_unload(self):
        self.update_exchange_rate.cancel()
        self.init_tournament.cancel()
        self.run_tournament.cancel()
        self.backup_data.cancel()


    @tasks.loop(time=tourn_times)
    async def run_tournament(self):
        self.tournament = Tournament.from_save(self.tournament_path)
        self.tournament.run_day()
        self.tournament.save(self.tournament_path)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = "Some tournament results are in!\nType !scout to see how they're doing!"
                await channel.send(message)

        with open(self.user_path, "r") as f:
            users = json.load(f)

        with open(self.kitty_path, "r") as f:
            kitty = json.load(f)

        tournament_table = pd.DataFrame(self.tournament.fighter_info()).sort_values("mean_outcome")
        rankings = tournament_table["tourn_id"].tolist()
        output = ""
        for goblin in self.tournament.fighters:
            if goblin.manager != None:
                position = rankings.index(goblin.tourn_id)
                pre_payout = goblin.funding * goblin.winrate() * tournament_table.shape[0]/position
                payout = pre_payout * (1 - self.tax)
                kitty["tax"] += pre_payout - payout
                manager_id = discord.utils.get(self.bot.users, name=goblin.manager).id
                users[str(manager_id)]["GLD"] += payout
                goblin.earnings += payout

                output += f"{goblin.manager} earned {payout:,.2f} GLD from {goblin.name}'s performance!\n"


        with open(self.user_path, "w") as f:
            json.dump(users, f)

        with open(self.kitty_path, "w") as f:
            json.dump(kitty, f)

        if output != "":
            for guild in self.bot.guilds:
                channel = discord.utils.get(guild.text_channels, name=self.channel_name)
                if channel:
                    await channel.send(output)

        
                
    @tasks.loop(time=start_time)
    async def init_tournament(self):
        self.run_tournament.cancel()
        self.tournament = Tournament(participants=50,
                                        daily_combats=50,
                                        daily_mortalities=0,
                                        )
        with open(self.kitty_path, "r") as f:
            tax = json.load(f)["tax"]

        for fighter in self.tournament:
            fighter.funding += tax//10

        self.tournament.run_day()
        self.tournament.save(self.tournament_path)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"@everyone __It's {start_time.strftime('%H:%M')} UTC so the daily tournament has started!__\n\n \nYou have 30 minutes to choose any sponsorships!\n Call *!scout* to see the contestants, *!fund* to invest your gold and *!goblin goblin_id* to view a goblin's stats!"
                await channel.send(message)
        
        self.bot.accepting_sponsors = True
        await asyncio.sleep(1800)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"The sponsor window has now closed!\nThere will be {len(tourn_times)} combats per day. Sponsors will earn some GLD after each combat!"
                message += "\nFights are happening at:\n" + "\n".join([t.strftime("%H:%M") + " UTC" for t in tourn_times])
                await channel.send(message)

        self.bot.accepting_sponsors = False
        self.run_tournament.start()
        

    @tasks.loop(minutes=5)
    async def update_exchange_rate(self):

        with open(self.exchange_path, "r") as f:
            rates = json.load(f)
            previous_rates = rates.copy()

        new_rates = await currency_query(self.summoners, noise=False)
        new_rates_copy = new_rates.copy()

        ######### probably needs incorparating elsewhere eventually
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

        log_totals = {currency: np.log10(0.000001 + quantity) for currency, quantity in totals.items()}

        new_rates = {key: np.max((new_rates[key] - log_totals[key], 0.0001))
                       for key in totals.keys()}

        rates.update(new_rates)
        with open("rate_update.log", "a") as f:
            f.write(f"New Rates before circulation adjustment:{new_rates_copy}\nTotal of each currency in server: {totals}\nLogarithm of totals: {log_totals}\nUpdated rates: {new_rates}\n\n\n")
        
        with open(self.exchange_path, "w") as f:
            json.dump(rates, f)
        
        with open(self.history_path, "r") as f:
            history = json.load(f)
            str_time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            history[str_time] = rates

        with open(self.history_path, "w") as f:
            json.dump(history, f)

        if new_rates == previous_rates:
            return

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"Here are the new rates as of {str_time}:"
                embed = discord.Embed(title="Rate Update", color=0x00ff00, description=message)  # Green
                for pr, r in zip(previous_rates.items(), rates.items()):
                    if pr[0] != "GLD":
                        embed.add_field(name=pr[0], value=f"{pr[1]:.3f} -> {r[1]:.3f}", inline=True)

                await channel.send(embed=embed)

            else:
                print(f"Channel '{self.channel_name}' not found in '{guild.name}'.")

    @tasks.loop(time=backup_times)
    async def backup_data(self):
        source_directory = 'glicko_bot/cogs/data'
        backup_directory = 'glicko_bot/cogs/backup'
        
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

    @init_tournament.before_loop
    @run_tournament.before_loop
    @update_exchange_rate.before_loop
    @backup_data.before_loop
    async def before_background_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.bot):
        await bot.add_cog(Background(bot))