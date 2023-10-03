import discord
from discord.ext import commands, tasks
import json
import numpy as np
from ..modules.pets import *
from ..modules.time import *
from config import Auth
from ..modules import user_funcs, server_funcs, pet_funcs, exchange_funcs


class GachaPets(commands.Cog):
    """
    Hatch your own Virtual Pets!
    """

    def __init__(self, bot):
        self.bot = bot
        self.channel_name = "general" # channel to send updates to

        self.wellbeing.start()
        self.pet_state.start()

    def cog_unload(self):
        self.wellbeing.cancel()
        self.pet_state.cancel()

    @commands.command()
    async def gacha(self, ctx, 
                    stars: int=commands.parameter(description="The tier of egg to purchase.", default=1),
                    egg_type: str=commands.parameter(description="The type of egg to purchase.", default="standard")):
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
        
        wallet = await user_funcs.get_user_wallet(ctx.author)

        if wallet.get("GLD", 0) < price:
            await ctx.send(f"You dont have {price} GLD to buy a {stars} star egg!")
            return
        
        await user_funcs.update_wallet(ctx.author, "GLD", -price)
        
        pet = TYPES[egg_type](stars)
        pet.owner_id = str(ctx.author.name)
        current_pets = await pet_funcs.get_user_pets(ctx.author)
        n_current_pets = len(current_pets)
        pet.id = n_current_pets + 1
        await pet_funcs.create_pet_entry(ctx.author, pet) 
        await ctx.send(f"Congratulations! {ctx.author.name} hatched a **{str(pet)}**!This creature has a Rarity of {pet.rarity}\nType !name {len(pets[user])-1} <NAME> to give it a name!")

    @commands.command()
    async def name(self, ctx, 
                   pet_id: int = commands.parameter(description="The ID of your pet."),
                   pet_name: str = commands.parameter(description="The name to give your pet.")):
        """
        Give your pet a name!

        Example usage:
        !name 0 Joe
        """
        
        if len(pet_name) > 15:
            await ctx.send("Names can't be more than 15 characters!")
            return 
        
        pet = await pet_funcs.get_pet(ctx.author, pet_id)
        
        if not pet:
            await ctx.send("I can't find that pet...")
            return 

        if not pet.is_alive:
            await ctx.send(f"I'm sorry... this pet left us on {pet.deathday}\n**RIP**")
            return
        
        await pet_funcs.update_pet_field(ctx.author, pet_id, {"name":pet_name})
        await ctx.send(f"{str(ctx.author.name)}'s {str(pet)} is now called **{pet_name}**!")

    @commands.command()
    async def health(self, ctx, 
                   pet_id: int or str = commands.parameter(description="The ID of your pet.")):
        """
        Display information about your pet's wellbeing.

        Example usage:
        !health 0
        """
        kwargs = {"pet_id":None, "pet_name":None}
        if isinstance(pet_id, int):
            kwargs.update({"pet_id":pet_id})

        elif isinstance(pet_id, str):
            kwargs.update({"pet_name":pet_id})
        
        pet = await pet_funcs.get_pet(ctx.author, **kwargs)

        if not pet:
            await ctx.send("That pet doesn't exist...")

        if not pet.is_alive:
            await ctx.send(f"I'm sorry... this pet left us on {pet.deathday}\n**RIP**")
            return
        
        report = self.create_report(pet)
        await ctx.send(report)
    
    @commands.command()
    async def pets(self, ctx):
        """
        List all of your living pets!

        Example usage:
        !pets
        """
        pets = await pet_funcs.get_user_pets(ctx.author)
        embed = discord.Embed(title=f"{str(ctx.author.name)}'s Pets")
        for pet in pets:
            pet = Pet.from_dict(pet)
            if pet.is_alive:
                embed.add_field(name=str(pet) + f"({pet.id})", value=f"Age: {pet.get_age()} days\nRarity: {pet.rarity}")
        if len(embed.fields) > 0:
            await ctx.send(embed=embed)

    @commands.command()
    async def feed(self, ctx, 
                   pet_id: int = commands.parameter(description="The ID of your pet.")):
        """
        Feed your pet!

        Example usage:
        !feed 0
        """

        pet = await pet_funcs.get_pet(ctx.author, pet_id)

        if not pet:
            await ctx.send("That pet doesn't exist...")

        if not pet.is_alive:
            await ctx.send(f"I'm sorry... this pet left us on {pet.deathday}\n**RIP**")
            return

        required_food, food_cost = pet.get_food()

        wallet = await user_funcs.get_user_wallet(ctx.author)
        
        if wallet.get(["GLD"], 0) < food_cost:
            await ctx.send(f"You can't afford to buy {required_food} for {pet.name}...")
            return
        
        await user_funcs.update_wallet(ctx.author, "GLD", -food_cost)
        pet.get_food()
        pet.feed()

        await pet_funcs.update_pet_field(ctx.author, pet_id, pet.__dict__)
        await ctx.send(f"You fed {pet.name} some {required_food}!")
            

    @commands.command()
    async def clean(self, ctx, 
                   pet_id: int = commands.parameter(description="The ID of your pet.")):
        """
        Clean your pet!

        Example usage:
        !clean 0
        """
        pet = await pet_funcs.get_pet(ctx.author , pet_id)
        if not pet:
            await ctx.send("That pet doesn't exist...")
            return

        if not pet.is_alive:
            await ctx.send(f"I'm sorry... this pet left us on {pet.deathday}\n**RIP**")
            return

        pet.clean()
        await pet_funcs.update_pet_field(ctx.author, pet_id, pet.__dict__)
        await ctx.send(f"{str(pet)} now looks spotless!")


    #5 TODO: !voodoo attempt to revive deceased pets if there is space
    #4 TODO: !graveyard list all deceased pets
    #3 TODO: !play raise their affection. Decreases over time. If affection is maxed, they dont want to play

    @tasks.loop(hours=2)
    async def wellbeing(self):
        """
        Loop to check the wellbeing of each pet every 2 hours.
        """
        pets = await pet_funcs.all_living_pets()

        for pet in pets:
            pet = Pet.from_dict(pet)
            stays_alive, cause = pet._death_check(return_cause=True)
            if not stays_alive:
                user = self.bot.get_user(pet.owner_id)
                bad_news = f"{pet.deathday}: {str(pet)} has sadly passed away due to {cause}.\n"
                await user.send(bad_news)

    @tasks.loop(hours=1)
    async def pet_state(self):
        """
        Update each pet's hunger, filth and affection every hour.
        If they are alive and need attention, message the owner.
        """
        pets = await pet_funcs.all_living_pets()
        for pet in pets:
            pet = Pet.from_dict(pet)
            user = self.bot.get_user(pet.owner_id)
            pet.hunger += 1
            pet.filth += 4
            pet.affection -= 1

            if pet.affection > MAX_AFFECTION:
                pet.affection = MAX_AFFECTION
            elif pet.affection < 0:
                pet.affection = 0
            
            if pet.filth > MAX_FILTH:
                pet.filth = MAX_FILTH
            elif pet.filth < 0:
                pet.filth = 0

            await pet_funcs.update_pet_field(user, pet.id, pet.__dict__)

    @pet_state.before_loop
    @wellbeing.before_loop
    async def before_background_task(self):
        await self.bot.wait_until_ready()

    @staticmethod
    def create_report(pet: Pet) -> str:
        report = f"Age: {pet.get_age()} days\nTemperament: {pet.personality}\nFavourite Food: {PET_SPECIES[pet.species]['food']}\n"

        # Hunger checks
        thresh = HUNGER_THRESH
        if pet.is_ghost:
            thresh = GHOST_HUNGER_THRESH
        
        for val, adv in HUNGER_ADVERBS.items():
            if pet.hunger >= (thresh * val):
                report += f"They are *{adv} hungry*.\n"
                break
        
        # Affection checks
        for val, adv in AFFECTION_ADJECTIVES.items():
            if pet.affection/MAX_AFFECTION >= val:
                report += f"They are feeling *{adv}*.\n"
                break
        
        # Filth checks
        for val, adv in FILTH_ADJECTIVES.items():
            if pet.filth/MAX_FILTH >= val:
                report += f"They look *{adv}*.\n"
                break
        
        if len(report) > 0:
            return f"\n**{str(pet)}** ({pet.id})\n" + report
        return False


async def setup(bot: commands.bot):
        await bot.add_cog(GachaPets(bot))