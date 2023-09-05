"""
Sponsor Goblin Fighters with your Gold. 
Earn more gold as they compete!
"""

import discord
from discord.ext import commands
import json
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io

from ..modules.time import tourn_times, start_time, scout_duration

from glicko_goblins.combat import Tournament

sns.set_theme()


class Sponsor(commands.Cog):

    """
    Sponsor Goblins like Gobbo to fight 1v1 in the Arena.
    Sponsor's earn Gold as their goblins progress through tournaments.
    """

    def __init__(self, bot):
        self.bot = bot
        self.tournament_path = "glicko_goblins/data/tournament.pkl"
        self.user_path = "glicko_bot/data/users.json"

    @commands.command()
    async def times(self, ctx):
        """
        Display the times of tournaments and tournament rounds.

        Example usage:
        !times
        """
        
        embed = discord.Embed(title="Today's Tournament Schedule", description=f"Scout duration: {scout_duration//60} Minutes", color=0xf803fc)
        n_tourns = len(start_time)
        total_rounds = len(tourn_times)
        rounds_per_tourn = total_rounds//n_tourns

        for tourn_number, timewindow in enumerate(range(0, total_rounds, rounds_per_tourn)):
            window = tourn_times[timewindow:timewindow + rounds_per_tourn]
            name = f"Tournament {tourn_number + 1}\nStart Time: {start_time[tourn_number].strftime('%H:%M')}"
            value = "\n".join([f"Round {i} > {round.strftime('%H:%M')}" for i, round in enumerate(window, start=1)])
            embed.add_field(name=name, value=value)
        
        await ctx.send(embed=embed)

    @commands.command()
    async def scout(self, ctx, my_fighters: str = commands.parameter(description="Add 'me' if you only want to display fighters you manage!", default=None)):
            """
            View the tournament participants.

            Example usage:
            !scout
            !scout me
            """
            if not os.path.exists(self.tournament_path):
                await ctx.send("There isn't an ongoing tournament right now!")
                return
            
            goblins = pd.DataFrame(Tournament.from_save(self.tournament_path).fighter_info())
            goblins["losses"] = goblins["total_games"] - goblins["wins"]
            goblins = goblins[["tourn_id", "name", "manager", "funding", "earnings", "rating", "rating_deviation"]]

            if my_fighters == "me":
                 author = ctx.message.author.name
                 goblins = goblins.query(f"manager == '{author}'")

            split_size = 10
            num_splits = (len(goblins) + split_size - 1) // split_size

            # Split the original DataFrame into smaller DataFrames
            for i in range(num_splits):
                start_idx = i * split_size
                end_idx = (i + 1) * split_size
                await ctx.send(f"```\n{goblins[start_idx:end_idx].to_markdown(index=False)}\n```")
            
    @commands.command(aliases=["stats"])
    async def goblin(self, ctx,  tourn_id: float = commands.parameter(description="The tourn_id of a goblin.")):
        """
        Display the stats of a goblin in a tournament.

        Example usage:
        !goblin 56
        """
        if not os.path.exists(self.tournament_path):
            await ctx.send("There isn't an ongoing tournament right now!")
            return
        
        tourn = Tournament.from_save(self.tournament_path)
        for goblin in tourn.fighters:
            if goblin.tourn_id == tourn_id:
                fig = goblin.plot_base_stats()
                buf = io.BytesIO()
                plt.savefig(buf)
                buf.seek(0)
                await ctx.send("Fighter breakdown:", file=discord.File(buf, "goblin.png"))
                plt.close()
                break

    @commands.command()
    async def roster(self, ctx):
        """
        Display the performance metrics of your active roster!

        Example usage:
        !roster
        """
        if not os.path.exists(self.tournament_path):
            await ctx.send("There isn't an ongoing tournament right now!")
            return
        current_tourn = Tournament.from_save(self.tournament_path)
        goblins = pd.DataFrame(current_tourn.fighter_info())
        author = ctx.message.author.name
        goblins.query(f"manager == '{author}'", inplace=True)
        goblins["losses"] = goblins["total_games"] - goblins["wins"]
        goblins["biggest_hit"] = goblins["damage_instances"].map(lambda x: max(x, default=0))
        goblins = goblins[["tourn_id", 
                           "name", 
                           "funding", 
                           "earnings", 
                           "rating", 
                           "rating_deviation",
                            "total_games",
                            "swings",
                            "guards_broken",
                            "successful_guards",
                            "failed_guards",
                            "attacks_parried",
                            "times_parried_by_opponent",
                            "critical_hits",
                            "attacks_dodged",
                            "biggest_hit",
                            ]]
        await ctx.send(f"**{author}**'s current roster for {current_tourn.tournament_name}:")
        for row_dict in goblins.to_dict(orient="records"):
            embed = discord.Embed(title=f"{row_dict['name']}")
            for k,v in row_dict.items():
                if k != "name":
                    embed.add_field(name=k.title(), value=int(v))
            await ctx.send(embed=embed)
        
    @commands.command(aliases=["fund", "invest"])
    async def sponsor(self, ctx, tourn_id: float = commands.parameter(description="The tourn_id of a goblin."), new_funds: float = commands.parameter(description="How much GLD to sponsor!")):
        """
        Invest gold into Goblin Tournaments. Use !scout to see the options.

        Example usage:
        !sponsor 31 100
        """
        if not self.bot.accepting_sponsors:
            await ctx.send("Sponsorship for the current tournament is now closed!")
            return
        
        tourn = Tournament.from_save(self.tournament_path)
        with open(self.user_path, "r") as f:
                        users = json.load(f)
        
        managers = [fighter["manager"] for fighter in tourn.fighter_info()]
        if managers.count(ctx.message.author.name) >= 3:
            await ctx.send("You can't sponsor more than 3 goblins per tournament!")
            return
        
        funding_cap = max([goblin.funding+1 for goblin in tourn.fighters])
        
        for goblin in tourn.fighters:
            if goblin.tourn_id == tourn_id:
                if goblin.manager == None:
                    current_funds = goblin.funding
                    user_funds = users[str(ctx.message.author.id)]["GLD"]

                    if user_funds < current_funds:
                        await ctx.send(f"You don't have enough GLD to sponsor {goblin.name} (tourn_id: {goblin.tourn_id}).\nTheir current funding is {goblin.funding}")
                        return
                    
                    if new_funds > user_funds:
                        await ctx.send(f"You don't have {new_funds} GLD!")
                        return
                    
                    if new_funds <= current_funds:
                        await ctx.send(f"{new_funds} isn't enough! {goblin.name} is already getting {current_funds}!\nPlease invest more...")
                        return
                    
                    if new_funds > funding_cap:
                        await ctx.send(f"The current funding cap for this tournament is {funding_cap}. Make sure your funding is less than or equal to this amount!")
                        return
                    
                    users[str(ctx.message.author.id)]["GLD"] -= new_funds
                    goblin.manager = ctx.message.author.name
                    goblin.funding = new_funds
                    await ctx.send(f"{ctx.message.author.name} succesfully sponsored {goblin.name} for {goblin.funding} GLD!")

                else:
                    await ctx.send(f"This goblin is already funded by {goblin.manager}")

        tourn.save(self.tournament_path)
        with open(self.user_path, "w") as f:
            json.dump(users,f)


async def setup(bot: commands.bot):
        await bot.add_cog(Sponsor(bot))