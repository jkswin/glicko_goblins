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
start_time = [datetime.time(hour=0, minute=35, tzinfo=utc),
              datetime.time(hour=12, minute=30, tzinfo=utc),
              datetime.time(hour=19, tzinfo=utc),
            ]

# When combats happen
tourn_times = [
               datetime.time(hour=1, minute=15, tzinfo=utc),
               datetime.time(hour=1, minute=50, tzinfo=utc), # GMT is 1 hour ahead of this
               datetime.time(hour=2, minute=15,tzinfo=utc),
               datetime.time(hour=2, minute=45, tzinfo=utc),
               datetime.time(hour=3, minute=15, tzinfo=utc),
    
               datetime.time(hour=13, minute=30, tzinfo=utc),
               datetime.time(hour=14, tzinfo=utc),
               datetime.time(hour=14, minute=30, tzinfo=utc), # GMT is 1 hour ahead of this
               datetime.time(hour=15, tzinfo=utc),
               datetime.time(hour=15, minute=35, tzinfo=utc),
               datetime.time(hour=16, tzinfo=utc),
    
               datetime.time(hour=19, minute=35, tzinfo=utc),
               datetime.time(hour=20, tzinfo=utc),
               datetime.time(hour=20, minute=30, tzinfo=utc), # GMT is 1 hour ahead of this
               datetime.time(hour=21, tzinfo=utc),
               datetime.time(hour=21, minute=30, tzinfo=utc),
               datetime.time(hour=22, tzinfo=utc),
               ]

backup_times = [datetime.time(hour=i, tzinfo=utc) for i in range(24) if i%6==0]

credit_times = [datetime.time(hour=18, minute=24, tzinfo=utc)]

class Background(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.channel_name = "general" # channel to send updates to

        self.update_exchange_rate.start()
        self.init_tournament.start()
        self.backup_data.start()
        self.run_tournament.start()#############
        self.credit.start()

        self.tournament = None
        self.accepting_sponsors = True
        self.tournament_path = "glicko_goblins/data/tournament.pkl"
        self.exchange_path = "glicko_bot/data/exchange.json"
        self.history_path = "glicko_bot/data/exchange_history.json"
        self.user_path = "glicko_bot/data/users.json"
        self.kitty_path = "glicko_bot/data/kitty.json"
        self.archive_path = "glicko_bot/data/archive"
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
        try:
            self.tournament = Tournament.from_save(self.tournament_path)
        except FileNotFoundError:
            # if the bot starts at a datetime where Tournament has not been created yet
            return
        
        self.tournament.run_day()
        self.tournament.save(self.tournament_path)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = "Some tournament results are in!\nType !scout to see how they're doing!\n"
                await channel.send(message)

        with open(self.user_path, "r") as f:
            users = json.load(f)

        with open(self.kitty_path, "r") as f:
            kitty = json.load(f)

        tournament_table = pd.DataFrame(self.tournament.fighter_info()).sort_values("mean_outcome")
        rankings = tournament_table["tourn_id"].tolist()
        output = "\n"
        total_round_tax = 0
        for goblin in self.tournament.fighters:
            if goblin.manager != None:
                position = rankings.index(goblin.tourn_id)
                pre_payout = (goblin.funding * goblin.winloss() * tournament_table.shape[0]/position)/(goblin.eagerness + len(start_time))
                payout = int(pre_payout * 0.5)
                tax = pre_payout - payout
                kitty["tax"] += tax
                total_round_tax += tax
                manager_id = str(discord.utils.get(self.bot.users, name=goblin.manager).id)
                if manager_id in users.keys():
                    users[manager_id]["GLD"] += payout
                    goblin.earnings += payout

                    output += f"**{goblin.manager}** earned **{payout:,.2f}** GLD from **{goblin.name}**'s performance!\n\n"
                else:
                    output += f"**{goblin.manager}** doesn't have a wallet and so {goblin.name}'s earnings were transferred to the state.\n\n"
                    kitty["tax"] += payout
                    total_round_tax += payout

        output += f"\n{total_round_tax} GLD was paid to the state in Tournament fairs."
        self.tournament.save(self.tournament_path)
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
        if self.tournament is not None:
            str_time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            path = f"archive_tourn_{str_time}.json"
            self.tournament.save_dict(path)

        self.tournament = Tournament(participants=70,
                                        daily_combats=50,
                                        daily_mortalities=0,
                                        )
        with open(self.kitty_path, "r") as f:
            tax = json.load(f)["tax"]

        for fighter in self.tournament.fighters:
            fighter.funding += int(np.log2(tax))

        self.tournament.run_day()
        self.tournament.daily_combats *= 2
        self.tournament.save(self.tournament_path)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"@everyone **A new tournament has started!**\n\nYou have **30 minutes** to choose any sponsorships!\nCall *!scout* to see the contestants, *!fund* to invest your gold and *!goblin goblin_id* to view a goblin's stats!\nThe current results are based on pre-tournament matches. Choose wisely!"
                await channel.send(message)
        
        self.bot.accepting_sponsors = True
        await asyncio.sleep(1800)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"The sponsor window has now closed!\nThere will be **{len(tourn_times)//len(start_time)}** rounds per tournament and {len(start_time)} tournaments today. Each round will be {self.tournament.daily_combats} battles.\nSponsors will earn some GLD after each combat!"
                message += "\nTournament fights are happening today at:\n" + "\n".join([t.strftime("%H:%M") + " UTC" for t in tourn_times])
                await channel.send(message)

        self.bot.accepting_sponsors = False
        
    @tasks.loop(seconds=125)
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

        log_totals = {currency: np.log10(1 + quantity) for currency, quantity in totals.items()}

        new_rates = {key: np.max((new_rates[key] - log_totals[key], 0.0001))
                       for key in totals.keys()}

        rates.update(new_rates)
        str_time = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        with open("rate_update.log", "a") as f:
            f.write(f"{str_time}\nNew Rates before circulation adjustment:{new_rates_copy}\nTotal of each currency in server: {totals}\nLogarithm of totals: {log_totals}\nUpdated rates: {new_rates}\n\n\n")
        
        with open(self.exchange_path, "w") as f:
            json.dump(rates, f)
        
        with open(self.history_path, "r") as f:
            history = json.load(f)
            history[str_time] = rates

        with open(self.history_path, "w") as f:
            json.dump(history, f)

        # suppress posting rating updates if there isn't a change of more than 0.5% anywhere
        if all([np.absolute(new_rates[curr] - previous_rates[curr]) < previous_rates[curr]/200 
                for curr in new_rates.keys()]):
            return

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
        with open(self.user_path, "r") as f, open(self.kitty_path, "r") as f2:
            users = json.load(f)
            tax_pool = json.load(f2)
        
        user_golds = {user:self.wallet_to_gold(g) for user, g in users.items()}
        total_credit = tax_pool["tax"]//200
        users_total = sum(user_golds.values())
        payouts = {k:(1-(v/users_total))*total_credit for k,v in user_golds.items()}
        
        for user in payouts:
            users[user]["GLD"] += payouts[user]
        
        tax_pool["tax"] -= total_credit

        with open(self.user_path, "w") as f:
            json.dump(users, f)
           
        with open(self.kitty_path, "w") as f:
            json.dump(tax_pool, f)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"@everyone Credit has been distributed. Check your wallets!"
                await channel.send(message)

    def load_exchange_data(self):
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