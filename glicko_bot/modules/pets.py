import datetime
import numpy as np
import random

PET_SPECIES = {
    "dog":              {"min_age": 10, "max_age": 13, "food": "rodents", "rarity": 10},
    "cat":              {"min_age": 15, "max_age": 20, "food": "fish", "rarity": 10},
    "goldfish":         {"min_age": 5, "max_age": 10, "food": "insects", "rarity": 10},
    "parrot":           {"min_age": 15, "max_age": 80, "food": "seeds", "rarity": 5},
    "hamster":          {"min_age": 2, "max_age": 3, "food": "vegetables", "rarity": 10},
    "guinea pig":       {"min_age": 5, "max_age": 8, "food": "vegetables", "rarity": 10},
    "rabbit":           {"min_age": 7, "max_age": 12, "food": "vegetables", "rarity": 10},
    "snake":            {"min_age": 10, "max_age": 30, "food": "rodents", "rarity": 5},
    "turtle":           {"min_age": 20, "max_age": 40, "food": "vegetables", "rarity": 0.2},
    "ferret":           {"min_age": 6, "max_age": 10, "food": "fish", "rarity": 1.5},
    "hedgehog":         {"min_age": 4, "max_age": 6, "food": "insects", "rarity": 1},
    "lizard":           {"min_age": 5, "max_age": 20, "food": "insects", "rarity": 8},
    "hermit crab":      {"min_age": 10, "max_age": 30, "food": "fish", "rarity": 3},
    "chinchilla":       {"min_age": 10, "max_age": 20, "food": "vegetables", "rarity": 3},
    "tarantula":        {"min_age": 10, "max_age": 25, "food": "insects", "rarity": 3},
    "cockatiel":        {"min_age": 15, "max_age": 25, "food": "seeds", "rarity": 3},
    "miniature pig":    {"min_age": 15, "max_age": 20, "food": "vegetables", "rarity": 2},
    "bearded dragon":   {"min_age": 10, "max_age": 15, "food": "insects", "rarity": 3.5},
    "pygmy goat":       {"min_age": 10, "max_age": 15, "food": "vegetables", "rarity": 1},
    "capybara":         {"min_age": 8, "max_age": 10, "food": "vegetables", "rarity": 0.15},
    "meerkat":          {"min_age": 10, "max_age": 14, "food": "rodents", "rarity": 0.15},
    "griffon":          {"min_age": 100, "max_age": 200, "food": "fantasy mix", "rarity": 0.1},
    "dragon":           {"min_age": 100, "max_age": 300, "food": "fantasy mix", "rarity": 0.1},
    "phoenix":          {"min_age": 1, "max_age": 10, "food": "fantasy mix", "rarity": 0.1},
    "pegasus":          {"min_age": 200, "max_age": 500, "food": "fantasy mix", "rarity": 0.1},
    "jackalope":        {"min_age": 100, "max_age": 150, "food": "fantasy mix", "rarity": 0.1},
}

PET_COLOURS = { "black":20, 
                "white":20,
                "red":15,
                "blue":10, 
                "green":10, 
                "yellow":9, 
                "orange":5, 
                "purple":5, 
                "pink":5,
                "golden":1,
            }

FOODS = {"seeds": 50,
         "vegetables": 100,
         "insects": 150,
         "rodents": 250,
         "fish": 300, 
         "fantasy mix": 1000,
         "ectoplasm": 1000,
}

PET_DESCRIPTIONS = {
    'dog': "Dogs are social animals that have evolved alongside humans for thousands of years. They exhibit a wide range of behaviors, from loyalty and pack bonding to hunting and herding.",
    'cat': "Cats are solitary hunters with a strong predatory instinct. They are known for their agility and grooming habits, and they often form independent relationships with their human companions.",
    'goldfish': "Goldfish are freshwater fish that thrive in calm, still waters. They are known for their bright colors and can display schooling behavior in groups.",
    'parrot': "Parrots are highly intelligent birds with colorful plumage. They are social and often mimic sounds and human speech, making them popular pets.",
    'hamster': "Hamsters are small rodents that are nocturnal and burrowing animals. They are known for storing food in their cheek pouches and spinning on exercise wheels.",
    'guinea pig': "Guinea pigs are social rodents native to South America. They are herbivores and often exhibit vocalizations and squeaks, especially when seeking attention or food.",
    'rabbit': "Rabbits are herbivorous mammals known for their fast breeding and burrowing behavior. They are social animals that communicate through body language.",
    'snake': "Snakes are reptiles that come in various species, some of which are venomous. They are carnivorous and use a combination of stealth and ambush tactics to catch prey.",
    'turtle': "Turtles are reptiles known for their protective shells. They are slow-moving, primarily aquatic, and some species can live both in water and on land.",
    'ferret': "Ferrets are carnivorous mammals known for their curiosity and playful behavior. They are often kept as pets and have a keen sense of smell for hunting.",
    'hedgehog': "Hedgehogs are nocturnal insectivores covered in spines. They are solitary animals that roll into a ball when threatened and can eat a variety of small prey.",
    'lizard': "Lizards are reptiles with diverse behaviors. Some are arboreal, while others are ground-dwelling. They exhibit various hunting strategies and basking behaviors.",
    'hermit crab': "Hermit crabs are crustaceans that use empty shells for protection. They scavenge for food and are known for their social behaviors and shell-swapping habits.",
    'chinchilla': "Chinchillas are small rodents native to South America. They are known for their soft fur and are crepuscular, being most active during dawn and dusk.",
    'tarantula': "Tarantulas are large spiders known for their silk-spinning abilities. They are solitary predators that primarily hunt insects and small arthropods.",
    'cockatiel': "Cockatiels are small parrots known for their crest of feathers on their heads. They are social and can be trained to mimic sounds and perform tricks.",
    'miniature pig': "Miniature pigs are domesticated pigs bred for smaller size. They are omnivorous and can be kept as pets, often displaying social and intelligent behaviors.",
    'bearded dragon': "Bearded dragons are reptiles native to Australia. They are diurnal and omnivorous, often displaying territorial and basking behaviors.",
    'pygmy goat': "Pygmy goats are small domesticated goats known for their social nature. They are herbivores and are often kept for their milk and companionship.",
    'capybara': "Capybaras are the largest rodents in the world and are native to South America. They are social animals that live in groups and are often found near water.",
    'meerkat': "Meerkats are small mongooses native to Africa. They live in social groups called mobs and are known for their sentry behaviors, standing on their hind legs to watch for predators.",
    'griffon': "Griffons are mythical creatures with the body of a lion and the head and wings of an eagle. They are often depicted as majestic and powerful guardians in folklore.",
    'dragon': "Dragons are legendary creatures with reptilian features, including scales and wings. They are often portrayed as fire-breathing and intelligent beings in mythology.",
    'phoenix': "Phoenixes are mythical birds that are said to burst into flames and be consumed by fire upon death, only to be reborn from their ashes. They symbolize renewal and immortality.",
    'pegasus': "Pegasuses are mythical winged horses known for their grace and beauty. They are often depicted as symbols of freedom and inspiration.",
    'jackalope': "Jackalopes are mythical creatures that resemble rabbits with antlers. They are often portrayed as elusive and mischievous beings in American folklore."
}

PET_PERSONALITIES = [
    'kind',
    'stubborn',
    'charming',
    'independent',
    'arrogant',
    'compassionate',
    'selfish',
    'confident',
    'anxious',
    'enthusiastic',
    'manipulative',
    'honest',
    'moody',
    'ambitious',
    'lazy',
    'optimistic',
    'pessimistic',
    'thoughtful',
    'reckless',
    'patient',
    'impulsive',
    'loyal',
    'narcissistic',
    'friendly',
    'introverted',
    'outgoing',
    'cautious',
    'spontaneous',
    'critical',
    'empathetic'
]

PET_DATE_STRF = "%d-%m-%y_%H-%M-%S"

GHOST_HUNGER_THRESH = 12
HUNGER_THRESH = 48
FULLNESS_GAINED = 12

MAX_AFFECTION = 100
MAX_FILTH = 100

HUNGER_ADVERBS = {  0.25: "quite",
                    0.5: "pretty",
                    0.75: "very",
                    1: "dangerously",
                 }
AFFECTION_ADJECTIVES = {    0.25: "neglected",
                            0.5: "okay",
                            0.75: "happy",
                            1: "ecstatic",
                        }
FILTH_ADJECTIVES = {0.25: "clean",
                    0.5: "scruffy",
                    0.75: "dirty",
                    1: "filthy",
                 }

class Pet:

    def __init__(self, owner: str or None = None):
        
        self.owner = owner
        self.name = ""
        self.species = self._get_species()
        self.colour = self._get_colour()
        self.rarity = self._get_rarity()
        self.personality = self._get_personality()
        self.birthday = self.str_date_now()
        self.deathday = False
        self.cause_of_death = False
        self.id = False

        self.hunger = 0
        self.last_meal = self.birthday
        self.is_alive = True
        self.is_ghost = False
        self.n_deaths = 0
        self.filth = 0
        self.affection = 0

        self.memory = []
        self.conversation_history = False

        self._init_odds()

    def commit_conversation_to_memory(self):
        return
    
    def reply(self):
        return "..."

    def _death_check(self, return_cause:bool=False):
        cause = ""
        pre_check = self.is_alive

        if self.is_ghost:
            if self.hunger > GHOST_HUNGER_THRESH:
                self.is_alive = False
                cause = "ghostly hunger"

        if self.hunger > HUNGER_THRESH:
            if self.coin_toss():
                self.is_alive = False
                cause = "hunger"

        if self.get_age() > PET_SPECIES[self.species]["max_age"]:
            self.is_alive = False
            cause = "old age"

        elif self.get_age() > PET_SPECIES[self.species]["min_age"]:
            if self.coin_toss():
                self.is_alive = False
                cause = "old age"

        if self.filth > MAX_FILTH/2:
            if self.one_in(MAX_FILTH - self.filth + 1):
                self.alive = False
                cause = "disease"

        if pre_check != self.is_alive:
            self.n_deaths += 1

        if not self.is_alive and not self.is_ghost:
            self.deathday = self.str_date_now()

        if return_cause:
            return (self.is_alive, cause)

        return self.is_alive
    
    def _init_odds(self):
        self.species_odds = PET_SPECIES[self.species]["rarity"]
        self.colour_odds = PET_COLOURS[self.colour]
        self.odds = (self.species_odds/100) * (self.colour_odds/100)

    def _get_species(self):
        return random.choices(list(PET_SPECIES.keys()), weights=[p["rarity"] for p in PET_SPECIES.values()])[0]

    def _get_colour(self):
        return random.choices(list(PET_COLOURS.keys()), weights=list(PET_COLOURS.values()))[0]
    
    def _get_personality(self):
        return random.choice(PET_PERSONALITIES)
    
    def __str__(self) -> str:
        zomb = ""
        with_name = ""
        if self.is_ghost:
            zomb = "Ghost "
        if self.name != "":
            with_name = " the "

        return f"{self.name}{with_name}{self.colour.title()} {zomb}{self.species.title()}"
        
    def get_age(self):
        return (datetime.datetime.now() - 
                datetime.datetime.strptime(self.birthday, PET_DATE_STRF)).days
    
    def give_name(self, name:str):
        self.name = name

    def feed(self):
        self.hunger -= FULLNESS_GAINED
        self.last_meal = datetime.datetime.now().strftime(PET_DATE_STRF)
        if self.hunger < 0:
            self.hunger = 0

    def get_food(self):
        if self.is_ghost:
            food_source = "ectoplasm"
        else:
            food_source = PET_SPECIES[self.species]["food"]
            
        food_price = FOODS[food_source]
        return food_source, food_price
    
    def voodoo(self):
        if not self.is_alive:
            if self.one_in(3):
                self.is_ghost = True
                self.is_alive = True

        return self.is_alive
    
    def _get_rarity(self):
        """Return rarity as value between 0 and 1000"""
        relative_colour_rarity = (100 - PET_COLOURS[self.colour]) * 10
        relative_species_rarity = (100 - PET_SPECIES[self.species]["rarity"]) * 10
        return (relative_colour_rarity + relative_species_rarity)//2
    
    @classmethod
    def from_dict(cls, pet_dict):
        ob = cls()
        for key in pet_dict:
            setattr(ob, key, pet_dict[key])
        return ob
    
    @staticmethod
    def one_in(n):
        return random.randint(1,n) == 1

    @staticmethod
    def coin_toss():
        return bool(random.randint(0,1))
    
    @staticmethod
    def str_date_now():
        return datetime.datetime.strftime(datetime.datetime.now(),
                                                   PET_DATE_STRF,
                                                   )

class Gacha:
    
    def standard_draw(stars:int=1):
        return sorted([Pet() for i in range(stars)], key=lambda x: x.odds)[0]
    
    def colour_draw(stars:int=1):
        return sorted([Pet() for i in range(stars)], key=lambda x: x.colour_odds)[0]
    
    def species_draw(stars:int=1):
        return sorted([Pet() for i in range(stars)], key=lambda x: x.species_odds)[0]