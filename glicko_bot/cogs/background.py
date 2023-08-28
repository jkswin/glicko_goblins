"""
The background workings that affect currency values.
"""


import discord
from discord.ext import commands, tasks
import json
import datetime
from glicko_goblins.combat import Tournament
import asyncio
from ..modules.currency_dependencies import currency_query
from dotenv import dotenv_values


cfg = dotenv_values(".env")
utc = datetime.timezone.utc
tourn_time = datetime.time(hour=21, tzinfo=utc)

class Background(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.channel_name = "general" # channel to send updates to

        self.update_exchange_rate.start()
        self.init_tournament.start()

        self.tournament = None
        self.accepting_sponsors = True
        self.tournament_path = "glicko_goblins/data/tournament.pkl"
        self.exchange_path = "glicko_bot/data/exchange.json"
        self.history_path = "glicko_bot/data/exchange_history.json"
        self.summoners = json.loads(cfg["SUMMONERS"])

    def cog_unload(self):
        self.update_exchange_rate.cancel()
        self.init_tournament.cancel()
        self.run_tournament.cancel()


    @tasks.loop(time=tourn_time)
    async def run_tournament(self):
        self.tournament.run_day()
        self.tournament.save(self.tournament_path)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = "Today's tournament results are in!"
                await channel.send(message)
        #TODO: Payout based on if anyone sponsored goblins. 
        # Goblins have a "manager" and "funding".
        # The sponsor must be greater than the initial funding.
        
    @tasks.loop(hours=72)
    async def init_tournament(self):
        self.run_tournament.cancel()
        self.tournament = Tournament(participants=150,
                                        daily_combats=50,
                                        daily_mortalities=0,
                                        )
        self.tournament.run_day()
        self.tournament.save(self.tournament_path)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = "A new tournament has started!\nYou have 1 hour to choose any sponsorships!"
                await channel.send(message)
        
        self.accepting_sponsors = True
        await asyncio.sleep(3600)
        self.accepting_sponsors = False
        self.run_tournament.start()
        

    @tasks.loop(minutes=15)
    async def update_exchange_rate(self):

        with open(self.exchange_path, "r") as f:
            rates = json.load(f)
            previous_rates = rates.copy()

        new_rates = await currency_query(self.summoners)
        rates.update(new_rates)

        with open(self.exchange_path, "w") as f:
            json.dump(rates, f)
        
        with open(self.history_path, "r") as f:
            history = json.load(f)
            history[datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")] = rates

        with open(self.history_path, "w") as f:
            json.dump(history, f)

        for guild in self.bot.guilds:
            channel = discord.utils.get(guild.text_channels, name=self.channel_name)
            if channel:
                message = "Here are the new rates:"
                embed = discord.Embed(title="Hourly Rate Update", color=0x00ff00, description=message)  # Green
                for pr, r in zip(previous_rates.items(), rates.items()):
                    if pr[0] != "GLD":
                        embed.add_field(name=pr[0], value=f"{pr[1]:.3f} -> {r[1]:.3f}", inline=True)

                await channel.send(embed=embed)

            else:
                print(f"Channel '{self.channel_name}' not found in '{guild.name}'.")

    @init_tournament.before_loop
    @run_tournament.before_loop
    @update_exchange_rate.before_loop
    async def before_background_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.bot):
        await bot.add_cog(Background(bot))