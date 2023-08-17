# Mini Project: Glicko Goblins :zombie:
Having recently been down the rabbit hole of rating systems, here I implement the Glicko rating system in the context of a probability-based combat simulation game between goblins in a thunderdome.

I recommend the following two papers as both sources of my implementation and very interesting reads:
- [A Comprehensive Guide to Chess Ratings, Glickman](http://www.glicko.net/research/acjpaper.pdf)
- [The Glicko System, Glickman](http://www.glicko.net/glicko/glicko.pdf)

TLDR; the Glicko system aims to fix a shortcoming of the Elo system, being the reliability of a player's rating. It introduces a Standard Deviation metric to a player's rating and also a time-axis such that the reliability of a player's rating decays with time away from play. 

That being said, unlike Elo it cannot be used to effectively order players by skill, as it describes a range that a player's hidden "skill" parameter is likely to be in to a certain degree of confidence.

- The 'Goblins' can be found [here](glicko_goblins/goblins.py)
    - Each Goblin has HP, Strength, Cooldown, Parry Probability, Guard Probability, Guardbreak Probability and Eagerness. 
    - Certain stats have direct relationships with others and have been v briefly shown in [this notebook](glicko_goblins/goblin_stats.ipynb) alongside rating correlation trends.

    
- The Tournament logic is found in [combat.py](glicko_goblins/combat.py)
    - Tournaments have a number of contestants, a number of days they run for and a number of combats per day. Contestants are selected each day based on their distributions of eagerness. Selected players are sorted by rating and matched against the next closest opponent. 
    - Contestants can participate in multiple combats per day or not participate at all. If a participant does not participate, they get progressively 'rustier' the more days that pass. 

- The Rating System itself is found in [glicko.py](glicko_goblins/glicko.py)
    - The time period after which the players' ratings are updated is 1 tournament day. 