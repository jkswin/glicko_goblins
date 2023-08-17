import numpy as np
from configs import C

"""
Glicko Rating System
http://www.glicko.net/glicko/glicko.pdf pp3-4
"""

# constant
Q = np.log(10)/400

def step1_rd(previous_rd, c=C):
    rd = np.sqrt(previous_rd**2 + c**2)
    return np.clip(rd, a_min=30, a_max=350)

def r_dash(previous_rating, rd, opponent_ratings, opponent_rds, outcomes, d2):
    return previous_rating + (Q/((1/rd**2) + 1/d2)) * \
        np.sum([g_rd(rdj)*(sj - expectation_j(previous_rating, rj, rdj)) 
                for rj, rdj, sj in zip(opponent_ratings, opponent_rds, outcomes)])

def rd_dash(rd, d2): 
    return np.sqrt(1/((1/rd**2) + (1/d2)))

def g_rd(rd):
    return 1/(np.sqrt(1 + (3*Q**2) * (rd**2)/np.pi**2))

def expectation_j(r, rj, rdj):
    return 1/(1+ 10**(-1 * g_rd(rdj)*(r-rj)/400))

def calc_d2(opponent_rds, opponent_ratings, r):
    return 1/(Q**2 * np.sum(
        [(g_rd(rdj)**2) * expectation_j(r, rj, rdj)*(1-expectation_j(r, rj, rdj)) for rj, rdj in zip(opponent_ratings, opponent_rds)])
        )

def player_update(previous_rating, rd, game_history):
    rd = step1_rd(rd)
    if len(game_history) == 0:
        return previous_rating, rd

    opponent_ratings = []
    opponent_rds = []
    game_outcomes = []
    for game in game_history:
        opponent_ratings.append(game["opponent_rating"])
        opponent_rds.append(game["opponent_rd"])
        game_outcomes.append(int(game["win"]))

    d2 = calc_d2(opponent_rds, opponent_ratings, previous_rating)
    return r_dash(previous_rating, rd, opponent_ratings,opponent_rds,game_outcomes, d2), \
            rd_dash(rd, d2)


if __name__ == "__main__":
    print(f"Q: {Q}\nC: {C}")