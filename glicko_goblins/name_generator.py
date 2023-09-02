import numpy as np
from random import shuffle, choice


from .configs import *

def generate_names():
    combinations = []
    
    for name1 in PLACEHOLDER_NAMES:
        for name2 in PLACEHOLDER_NAMES:
            for numeral in NUMERALS:
                full_name = f"{name1} {name2} {numeral}"
                combinations.append(full_name)
    
    shuffle(combinations)
    return combinations

def generate_tournament_name() -> str:
    return f"The {choice(TOURN_TITLES)} {choice(TOURN_TYPES)}"




