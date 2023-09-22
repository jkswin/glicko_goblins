import discord
from discord.ext import commands, tasks
import json
import numpy as np
from ..modules.pets import *
from ..modules.time import *
from dotenv import dotenv_values


cfg = dotenv_values(".env")


class GachaPets(commands.Cog):
    """
    Hatch your own Virtual Pets!
    """

    def __init__(self, bot):
        self.bot = bot
        self.channel_name = "general" # channel to send updates to

        self.wellbeing.start()
        self.pet_state.start()

        self.USER_PATH = "glicko_bot/data/users.json"
        self.KITTY_PATH = "glicko_bot/data/kitty.json"
        self.PET_PATH = "glicko_bot/data/pets.json"
        self.SUMMONERS = json.loads(cfg["SUMMONERS"])

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

        if sum([int(Pet.from_dict(p).is_alive) for p in pets[user]]) > 5:
            await ctx.send("Your enclosure is only big enough to hold 5 pets!")
            return 
        
        pet.id = len(pets[user])
        pet.owner = str(ctx.author.name)
        pets[user].append(pet.__dict__)

        with open(self.PET_PATH, "w") as f:
            json.dump(pets,f)
        
        with open(self.USER_PATH, "w") as f:
            json.dump(wallets,f)

        await ctx.send(f"Congratulations! {pet.owner} hatched a **{str(pet)}**!This creature has a Rarity of {pet.rarity}\nType !name {len(pets[user])-1} <NAME> to give it a name!")

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
        
        pet = Pet.from_dict(pets[user][pet_id])

        if not pet.is_alive:
            await ctx.send(f"I'm sorry... this pet left us on {pet.deathday}\n**RIP**")
            return

        pre_str = str(pet)
        pet.give_name(pet_name)
        pets[user][pet_id] = pet.__dict__

        with open(self.PET_PATH, "w") as f:
            json.dump(pets,f)

        await ctx.send(f"{str(ctx.author.name)}'s {pre_str} is now called **{pet_name}**!")

    @commands.command()
    async def health(self, ctx, 
                   pet_id: int = commands.parameter(description="The ID of your pet.")):
        """
        CURRENTLY DOES NOTHIN! 
        Display information about your pet's wellbeing.

        Example usage:
        !health 0
        """

        # Show their name, birthday, age, hunger level, cleanliness, mood, personality
        return
    
    @commands.command()
    async def pets(self, ctx):
        """
        List all of your living pets!

        Example usage:
        !pets
        """
        user = str(ctx.author.id)
       
        with open(self.PET_PATH, "r") as f:
            pets = json.load(f)

        if user not in pets.keys():
            await ctx.send("You don't have any pets!")
            return 
        
        embed = discord.Embed(title=f"{str(ctx.author.name)}'s Pets")
        for pet in pets[user]:
            pet = Pet.from_dict(pet)
            if pet.is_alive:
                embed.add_field(name=str(pet), value=f"Age: {pet.get_age()} days\nRarity: {pet.rarity}")

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
        user = str(ctx.author.id)
       
        with open(self.PET_PATH, "r") as f:
            pets = json.load(f)
        
        if user not in pets.keys():
            await ctx.send("You don't have any pets!")
            return 
        
        if pet_id >= len(pets[user]) or pet_id < 0:
            await ctx.send("You don't own a pet with that ID!")
            return
        
        pet = Pet.from_dict(pets[user][pet_id])

        if not pet.is_alive:
            await ctx.send(f"I'm sorry... this pet left us on {pet.deathday}\n**RIP**")
            return

        ####
        required_food, food_cost = pet.get_food()
  
        with open(self.USER_PATH, "r") as f:
            wallets = json.load(f)

        if user in wallets:
            if wallets[user]["GLD"] < food_cost:
                await ctx.send(f"You can't afford to buy {required_food} for {pet.name}...")
                return
            wallets[user]["GLD"] -= food_cost
            pet.get_food()
            pet.feed()
            await ctx.send(f"You fed {pet.name} some {required_food}!")
            
        else:
            await ctx.send("You don't have a wallet!")
            return
        ####

        pets[user][pet_id] = pet.__dict__

        with open(self.PET_PATH, "w") as f:
            json.dump(pets,f)

  
    #3 TODO: !health, show birthday and also use Pet.get_age()
    #5 TODO: !voodoo attempt to revive deceased pets if there is space
    #4 TODO: !graveyard list all deceased pets
    #3 TODO: !play raise their affection. Decreases over time. If affection is maxed, they dont want to play
    #2 TODO: !clean reduce Pet.filth. Increases over time

    @tasks.loop(hours=2)
    async def wellbeing(self):
        """
        Loop to check the wellbeing of each pet every 2 hours.
        """
        with open(self.PET_PATH, "r") as f:
            pet_log = json.load(f)

        for owner_id, pet_list in pet_log.items():
            user = self.bot.get_user(int(owner_id))
            output = []
            for pet in pet_list:
                pet = Pet.from_dict(pet)
                if pet.is_alive:
                    stays_alive, cause = pet._death_check(return_cause=True)
                    if not stays_alive:
                        bad_news = f"{pet.deathday}: {str(pet)} has sadly passed away due to {cause}.\n"
                        await user.send(bad_news)
                output.append(pet.__dict__)

            pet_log[owner_id] = output
        
        with open(self.PET_PATH, "w") as f:
            json.dump(pet_log,f)

        return
    
    @tasks.loop(hours=1)
    async def pet_state(self):
        """
        Update each pet's hunger, filth and affection every hour.
        If they are alive and need attention, message the owner.
        """
        with open(self.PET_PATH, "r") as f:
            pet_log = json.load(f)

        for owner_id, pet_list in pet_log.items():
            user = self.bot.get_user(int(owner_id))
            report = False
            output = []
            for pet in pet_list:
                pet = Pet.from_dict(pet)

                if pet.is_alive:
                    pet.hunger += 1
                    pet.filth += 1
                    pet.affection -= 1

                    if pet.affection > MAX_AFFECTION:
                        pet.affection = MAX_AFFECTION
                    elif pet.affection < 0:
                        pet.affection = 0
                    
                    if pet.filth > MAX_FILTH:
                        pet.filth = MAX_FILTH
                    elif pet.filth < 0:
                        pet.filth = 0

                    if any([(pet.hunger >= HUNGER_THRESH//2 and not pet.is_ghost), 
                            (pet.hunger >= GHOST_HUNGER_THRESH//2 and pet.is_ghost),
                            (pet.filth >= MAX_FILTH//2),
                            (pet.affection <= pet.affection//2),
                            ]):
                            report = self.create_report(pet)

                output.append(pet.__dict__)

            pet_log[owner_id] = output

            if report:
                await user.send(report)
        
        with open(self.PET_PATH, "w") as f:
            json.dump(pet_log,f)
    
    @pet_state.before_loop
    @wellbeing.before_loop
    async def before_background_task(self):
        await self.bot.wait_until_ready()

    @staticmethod
    def create_report(pet: Pet) -> str:
        report = ""

        # Hunger checks
        thresh = HUNGER_THRESH
        if pet.is_ghost:
            thresh = GHOST_HUNGER_THRESH
        
        for val, adv in HUNGER_ADVERBS.items():
            if pet.hunger >= (thresh * val):
                report += f"Hunger: {adv} hungry.\n"
                break
        
        # Affection checks
        for val, adv in AFFECTION_ADJECTIVES.items():
            if pet.affection/MAX_AFFECTION >= val:
                report += f"Mood: {adv}\n"
                break
        
        # Filth checks
        for val, adv in FILTH_ADJECTIVES.items():
            if pet.filth/MAX_FILTH >= val:
                report += f"Cleanliness: {adv}\n"
                break
        
        if len(report) > 0:
            return f"\n**{str(pet)}** ({pet.id})\n" + report
        return False


async def setup(bot: commands.bot):
        await bot.add_cog(GachaPets(bot))