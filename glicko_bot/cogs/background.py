import discord
from discord.ext import commands, tasks
import datetime
from glicko_goblins.combat import Tournament
import asyncio
import numpy as np
from ..modules.currency import currency_query
from ..modules.time import *
from ..modules import exchange_funcs, user_funcs, server_funcs
from config import Auth
import pandas as pd



class Background(commands.Cog):
    """
    Home of all background tasks.
    """
    def __init__(self, bot):
        self.bot = bot
        self.channel_name = "general" # channel to send updates to

        self.update_exchange_rate.start()
        self.init_tournament.start()
        self.run_tournament.start()
        self.credit.start()

        self.tournament = None
        self.accepting_sponsors = True
        self.tournament_path = "glicko_goblins/data/tournament.pkl"
        self.archive_path = "glicko_goblins/data/archive/"
        self.coin_config_path = "coin.cfg"
        self.tax = 0.02

    def cog_unload(self):
        self.update_exchange_rate.cancel()
        self.init_tournament.cancel()
        self.run_tournament.cancel()
        self.credit.cancel()

    @tasks.loop(time=tourn_times)
    async def run_tournament(self):
        """
        Run a tournament day that has been initialised. 
        """
        def logistic_mapping(x, N, k=0.2):
            return 2 * (1 + 1 / (1 + np.exp(-k *(x - N/2)))) - 2

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

        # convert the current tournament state to a dataframe for easy sorting
        tournament_table = pd.DataFrame(self.tournament.fighter_info()).sort_values("mean_outcome", ascending=False)
        # sort the tournament participants by ranking. (ranking by glicko isn't strictly sound, but does the job here)
        rankings = tournament_table["tourn_id"].tolist()
        
        manager_results = {}
        # loop through all the fighters
        for goblin in self.tournament.fighters:
            # calculate the payout
            # based on funding, WL ratio, relative position based on ranking, eagerness to fight and number of tournaments today
            position = rankings.index(goblin.tourn_id)
            n_fighters = len(self.tournament.fighters)

            ranking_factor = logistic_mapping(x=n_fighters - position, N=n_fighters, k=0.2)
            pre_payout = (goblin.funding * np.cbrt(goblin.recent_winloss) * ranking_factor)/len(start_time)
            
            # half of it goes to tax pool if goblin is managed; calc and update
            payout = int(pre_payout * 0.5)
            goblin.earnings += payout
            
            if goblin.manager != None:
                tax_taken = pre_payout - payout
                await server_funcs.update_tax(tax_taken)
                # add the amount earned by their sponsored golbins to the users wallets
                manager = discord.utils.get(self.bot.users, name=goblin.manager)
                await user_funcs.update_wallet(manager, "GLD", payout)

                perc_return = 100*payout/goblin.funding
                total_perc_return = 100 * goblin.earnings/goblin.funding
                # add each users' returns to the output string
                info_dict = {
                        "name": goblin.name,
                        "payout": payout,
                        "rank": position + 1,
                        "recent_winloss": goblin.recent_winloss,
                        "percent_return": int(perc_return), 
                        "total_percent_return": int(total_perc_return),
                    }
                
                if goblin.manager not in manager_results.keys():
                    manager_results[goblin.manager] = []
                    
                manager_results[goblin.manager].append(info_dict)


        for manager, goblins in manager_results.items():
            embed = discord.Embed(title=f"{self.tournament.tournament_name}-{manager}'s Roster")
            for goblin in goblins:
                embed_value = f"Round Payout:{goblin['payout']}\nCurrent Rank: {goblin['rank']}\nRound WL: {goblin['recent_winloss']}\n%Return:{goblin['percent_return']}\n%Total:{goblin['total_percent_return']}"
                embed.add_field(name=goblin["name"], value=embed_value)

            for guild in self.bot.guilds:
                channel = discord.utils.get(guild.text_channels, name=self.channel_name)
                if channel:
                    await channel.send(embed=embed)

        # save the updated tournament (goblin earnings were added to each goblin)
        self.tournament.save(self.tournament_path)


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
                                        daily_combats=50,
                                        daily_mortalities=10,
                                        )
        
        tax = await server_funcs.get_tax()

        for fighter in self.tournament.fighters:
            fighter.funding += int(tax**(5/9))

        # run one tournament day to generate preliminary ratings
        self.tournament.run_day()
        self.tournament.run_day()
        self.tournament.turnover = 0
        # triple the number of combats to make rounds more interesting than preliminary round
        self.tournament.daily_combats *= 6
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

        previous_rates = await exchange_funcs.get_current_rate()
        new_rates = await currency_query(self.coin_config_path)
        if previous_rates is None:
            previous_rates = {"GLD":1}
            previous_rates.update({k:0 for k in new_rates.items()})
        await exchange_funcs.update_exchange_rate(new_rates)

        # send a server message notifying of updated rates
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"*Note that updates of less than 10% are not shown*"
                embed = discord.Embed(title="Rate Update", color=0x00ff00, description=message)  # Green
                for pr, r in zip(previous_rates.items(), new_rates.items()):
                    if pr[0] != "GLD":
                        if abs(pr[1] - r[1]) > 0.1*r[1]:
                            embed.add_field(name=pr[0], value=f"{pr[1]:.3f} -> {r[1]:.3f}", inline=True)

                if embed.fields:
                    await channel.send(embed=embed)


    @tasks.loop(time=credit_times)
    async def credit(self):
        """
        Daily wallet top up for users using tax pot. 
        Users without much money get a much larger proportion.
        """

        tax_pool = await server_funcs.get_tax()
        wallets = await user_funcs.get_all_wallets()
        exchange_rates = await exchange_funcs.get_current_rate()

        user_golds = {user:self.wallet_to_gold(g, exchange_rates) for user, g in wallets.items()}
        total_credit = tax_pool//200
        users_total = sum(user_golds.values())

        # for each user, give them a proportion of the tax based on their relative proportion of all gold in existence.
        payouts = {k:((1-(v/users_total))**len(wallets.keys()))*total_credit for k,v in user_golds.items()}
   
        for user_id in payouts:
            member = self.bot.get_user(user_id)
            await user_funcs.update_wallet(member, "GLD", payouts[user_id])
        
        # update the tax pool
        await server_funcs.update_tax(-total_credit)

        # alert the server that everyone has been given credit
        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = f"@everyone Credit has been distributed. Check your wallets!"
                await channel.send(message)


    def wallet_to_gold(self, wallet: dict, exchange_rates: dict) -> float:
        """
        Takes a wallet, converts its contents to GLD and returns the value.
        """
        gold = 0
        for currency, quantity in wallet.items():
            gold += quantity * exchange_rates.get(currency, 0)
        return gold

    @credit.before_loop
    @init_tournament.before_loop
    @run_tournament.before_loop
    @update_exchange_rate.before_loop
    async def before_background_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.bot):
        await bot.add_cog(Background(bot))