import discord
from discord.ext import commands, tasks
import json
import datetime
import asyncio
import numpy as np
from ..modules.pets import *
from ..modules.time import *
from dotenv import dotenv_values
import pandas as pd
import os
import pytz


cfg = dotenv_values(".env")


class GachaPets(commands.Cog):
    """
    Entire Pet and Gacha System Logic
    """

    def __init__(self, bot):
        self.bot = bot
        self.channel_name = "general" # channel to send updates to

        self.wellbeing.start()

        self.TOURNAMENT_PATH = "glicko_goblins/data/tournament.pkl"
        self.EXCHANGE_PATH = "glicko_bot/data/exchange.json"
        self.HISTORY_PATH = "glicko_bot/data/exchange_history.json"
        self.USER_PATH = "glicko_bot/data/users.json"
        self.KITTY_PATH = "glicko_bot/data/kitty.json"
        self.ARCHIVE_PATH = "glicko_bot/data/archive/"
        self.PET_PATH = "glicko_bot/data/pets.json"
        self.SUMMONERS = json.loads(cfg["SUMMONERS"])

    def cog_unload(self):
        self.wellbeing.cancel()

    @commands.command()
    async def gacha(self, ctx, 
                    stars: int=commands.parameter(description="The tier of egg to purchase.", default=1),
                    egg_type: int=commands.parameter(description="The type of egg to purchase.", default="standard")):
        """
        Open an egg to hatch a Pet! Eggs come in different varieties.
        <standard> - randomly draws a pet
        <colour> - randomly draws a pet, prioritising colour rarity
        <species> - randomly draws a pet, prioritising species rarity

        Eggs cost 300 GLD. Pay extra to increase the star rating of the egg, increasing your chances of finding rare pets:
        1* - 300
        2* - 500
        3* - 700
        4* - 900
        5* - 1100

        Example usage:
        !gacha
        !gacha 3 colour
        !gacha species
        """
        TYPES = {"standard":Gacha.standard_draw, 
                 "colour":Gacha.colour_draw, 
                 "species":Gacha.species_draw,
                 }
        
        STAR_RANGE = list(range(1,6))
        
        price = (stars*300) - ((stars-1)*100)

        if (egg_type not in TYPES.keys()) or (stars not in STAR_RANGE):
            await ctx.send("You can only hatch <standard>, <colour> and <species> eggs between 1 and 5 stars.")
            return
        
        with open(self.USER_PATH, "r") as f:
            wallets = json.load(f)
        user = str(ctx.author.id)

        if user not in wallets.keys():
            await ctx.send("You don't have a wallet...")
            return
        
        if wallets[user]["GLD"] < price:
            await ctx.send(f"You dont have {price} GLD to buy a {stars} star egg!")
            return
        
        wallets[user]["GLD"] -= price
        
        pet = TYPES[egg_type](stars)
        
        with open(self.PET_PATH, "r") as f:
            pets = json.load(f)
        
        if user not in pets.keys():
            pets[user] = []
        
        pet.id = len(pets[user])
        pet.owner = str(ctx.author.name)
        pets[user].append(pet.__dict__)

        with open(self.PET_PATH, "w") as f:
            json.dump(pets,f)
        
        with open(self.USER_PATH, "w") as f:
            json.dump(wallets,f)

        await ctx.send(f"Congratulations! {pet.owner} hatched a {str(pet)}!\nType !name {len(pets[user])-1} <NAME> to give it a name!")

    
    @commands.command()
    async def name(self, ctx, 
                   pet_id: int = commands.parameter(description="The ID of your pet."),
                   pet_name: str = commands.parameter(description="The name to give your pet.")):
        """
        Give your pet a name!

        Example usage:
        !name 0 Joe
        """
        user = str(ctx.author.id)
       
        with open(self.PET_PATH, "r") as f:
            pets = json.load(f)
        
        if user not in pets.keys():
            await ctx.send("You don't have any pets!")
            return 
        
        if len(pet_name) > 15:
            await ctx.send("Names can't be more than 15 characters!")
            return 
        
        if pet_id >= len(pets[user]) or pet_id < 0:
            await ctx.send("You don't own a pet with that ID!")
            return
        
        pets[user][pet_id].give_name(pet_name)

        with open(self.PET_PATH, "w") as f:
            json.dump(pets,f)

        await ctx.send(f"{str(ctx.author.name)}'s {str(pets[user][pet_id])} is now called {pet_name}!")
     
        

    @tasks.loop(hours=1) #TODO: Add time from time.py
    async def wellbeing(self):
        """
        Check the health state of pets.
        """
        return

    @wellbeing.before_loop
    async def before_background_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.bot):
        await bot.add_cog(GachaPets(bot))