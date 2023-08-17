import numpy as np

# glicko variables
C = np.sqrt((350**2 - 200**2)/150)

# goblin creation distributions
# (mean, std, lower_bound, upper_bound)
STAT_DISTRIBUTIONS = {"hp":         (40, 12, 20, 60), 
                      "strength":   (20, 5, 10, 30), 
                      "cooldown":      (7, 3, 1, 12), 
                      "guard":      (0.5, 0.25, 0, 0.9),
                      }

COMBAT_MULTIPLIERS = {"vanilla": 1/4,
                      "guard": 1/8,
                      "guardbreak": 1/3,
                      "parry": 1/2,
                      "crit": 2
                      }

NUMERALS = ["", "I", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

PLACEHOLDER_NAMES = [
    "Snickerdoodle",
    "Grumbleflap",
    "Wartbucket",
    "Fizzlepop",
    "Squidney",
    "Bumblegut",
    "Toadfluff",
    "Moldysnot",
    "Rumblebelly",
    "Gobsmack",
    "Snaggletooth",
    "Noodlewhisker",
    "Crankyboots",
    "Picklefingers",
    "Squeakums",
    "Gobbledegook",
    "Mudwobble",
    "Jellybelch",
    "Snotnoodle",
    "Froggleflop",
    "Gobbledorf",
    "Noodlegrump",
    "Bogbottom",
    "Gigglesnort",
    "Wobblechomp",
    "Munchkin",
    "Fuzzywump",
    "Gobblenose",
    "Gigglefizz",
    "Sneezewort",
    "Stinkerbelle",
    "Moldysprocket",
    "Bumblewhisk",
    "Wartnibbler",
    "Snickerdust",
    "Gobbleflap",
    "Fizzlefuzz",
    "Gurglebum",
    "Snotwhistle",
    "Grumbletooth",
    "Squeezle",
    "Noodlebop",
    "Toadstool",
    "Munchkinella",
    "Rumblegurgle",
    "Bogsnuggle",
    "Picklegrin",
    "Gigglewobble",
    "Sneezesprocket",
    "Wobblewrench",
    "Froggleblip",
    "Jellybelly",
    "Squidgums",
    "Giggledrip",
    "Noodlepluck",
    "Gobblenibble",
    "Mudfizzle",
    "Bumbleburp",
    "Squeakernose",
    "Chucklebump"
]
