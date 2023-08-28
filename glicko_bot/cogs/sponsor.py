"""
Sponsor Goblin Fighters with your Gold. 
Earn more gold as they compete!
"""

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
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

from glicko_goblins.combat import Tournament
from glicko_goblins.goblins import Fighter

sns.set_theme()


class Sponsor(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.tournament_path = "glicko_goblins/data/tournament.pkl"

    @commands.command()
    async def scout(self, ctx):
            """
            Look at the stats of a Goblin.
            """
            # Display the current tournament.
            if not os.path.exists(self.tournament_path):
                  return
            
            goblins = pd.DataFrame(Tournament.from_save(self.tournament_path).fighter_info())
            goblins = goblins[["tourn_id", "name", "manager", "funding", "wins", "total_games"]]
            output_table = goblins.to_markdown(index=False)
            print(output_table)
            print(len(output_table)) #TODO 
            await ctx.send(output_table)
            
    

    @commands.cooldown(3, 7200, BucketType.user)
    @commands.command()
    async def sponsor(self, ctx):
          """
          
          """
          #JAKE remember to update the funding of the goblins that get sponsored.
          return

async def setup(bot: commands.bot):
        await bot.add_cog(Sponsor(bot))