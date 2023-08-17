from goblins import Fighter
from random import shuffle, choice
import numpy as np
import glicko
from tqdm import tqdm
import json
from name_generator import generate_names
import pickle 

class Tournament:

    def __init__(self, participants=1000, n_days=100, daily_combats=1000, daily_mortalities=5) -> None:
        self.possible_names = generate_names()
        self.participants = participants
        self.fighters = [Fighter(name=self.possible_names.pop(0), entry_day=0) for _ in range(participants)]
        self.deceased = []
        self.daily_combats = daily_combats
        self.turnover = daily_mortalities
        self.n_days = n_days

    def run(self):
        for t in tqdm(range(self.n_days)):
            # each day represents matches occurring simultaneously
            contestants = self.hat_draw() #len(contestants) = self.simultaneous combats
            

            for f1, f2 in zip(contestants[::2], contestants[1::2]):
                combat = Combat(fighter1=self.fighters[contestants[f1]],
                                fighter2=self.fighters[contestants[f2]])
                combat.commence()

            # 5% die of their injuries after each day
            deaths = np.random.choice(range(self.participants-1), size=self.turnover)
            # sort to avoid indexing issues when calling pop
            deaths = sorted(deaths, reverse=True)
            for d in deaths:
                self.fighters[d].alive = False
                self.deceased.append(self.fighters.pop(d))

            # add that many new fighters into the mix
            [self.fighters.append(Fighter(name=self.possible_names.pop(0),entry_day=t+1)) for _ in range(self.turnover)]
            assert len(self.fighters) == self.participants

            # update each fighter's glicko score after each day
            for fighter_id, fighter in enumerate(self.fighters):
                if fighter_id in contestants:
                    fighter.time_since_last_combat = 0
                else:
                    fighter.time_since_last_combat +=1

                fighter.rating, fighter.rating_deviation = glicko.player_update(
                                                            fighter.rating, 
                                                            fighter.rating_deviation, 
                                                            fighter.games)

                # clear match history
                fighter.total_games += len(fighter.games)
                fighter.games = []

    @classmethod
    def from_save(cls, path:str):
        with open(path, "rb") as f:
            return pickle.load(f)

    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump(self, f)

    def hat_draw(self):

        # TODO: Optimise. Lots of repeated iterations
        # Create a list of indexes based on eagerness
        index_list = []
        for i, f in enumerate(self.fighters):
            # only choose alive ones
            if f.alive:
                index_list.extend([i] * f.eagerness)

        # Shuffle the index list to randomize selection
        shuffle(index_list)

        # Select indexes from the shuffled list 
        # making sure selected_fighters[i] != selected_fighters[i+1]
        selected_fighters = []
        current = -1
        for index in index_list:
            if len(selected_fighters) == 2 * self.daily_combats:
                break
            if index != current:
                current = index
                selected_fighters.append(index)

        # sort by rating so that similar rated players are paired against one another.
        # ensure that a player cannot face his/herself after reordering
        combined = list(zip(selected_fighters, [self.fighters[idx].rating for idx in selected_fighters]))
        sorted_indices = [combined[0][0]]
        for i in range(1, len(combined)):
            if combined[i][0] != sorted_indices[-1]:
                sorted_indices.append(combined[i][0])
            else:
                for j in range(i + 1, len(combined)):
                    if combined[j][0] != sorted_indices[-1]:
                        combined[i], combined[j] = combined[j], combined[i]
                        sorted_indices.append(combined[i][0])
                        break

        return sorted_indices
    
    def reset_ladder(self):
        for fighter in self.fighters:
            fighter.rating = 1500
            fighter.rating_deviation = 350

    def rating_interval(self):
        raise NotImplementedError("WIP: This is to be added in future.")

class Combat:
    def __init__(self, fighter1: Fighter, fighter2:Fighter) -> None:
        self.fighter1 = fighter1
        self.fighter2 = fighter2

    def commence(self):
        time = 0
        fighter_ids = [f for f in list(self.__dict__.keys()) if f.startswith("fighter") and f[-1].isdigit()]
        while True:
            time +=1 

            # shuffle the order of the fighters so that speed ties don't bias fighter 1
            shuffle(fighter_ids)

            # if the first fighter after randomization is off cooldown, swing
            if time % self.__dict__[fighter_ids[0]].cooldown == 0:
                self.__dict__[fighter_ids[0]].swing(self.__dict__[fighter_ids[1]])
                
                # check if either fighter is KOd
                if self._check_hps() > 0:
                    break

            # if the second fighter after randomization is off cooldown, swing
            if time % self.__dict__[fighter_ids[1]].cooldown == 0:
                self.__dict__[fighter_ids[1]].swing(self.__dict__[fighter_ids[0]])

                # check if either fighter is KOd
                if self._check_hps() > 0:
                    break
            
        winner = self._check_hps()
        self.fighter1.wins += int(winner==1)
        self.fighter2.wins += int(winner==2)

        self._record_game(winner, time)
        self.fighter1._reset()
        self.fighter2._reset()


    def _record_game(self, winner, time):
        """Add the game outcome to each fighter's games. Including game time."""

        self.fighter1.games.append(
            {"win":winner==1,
             "time":time,
             "current_n_games": len(self.fighter1.games),
             "opponent_rating":self.fighter2.rating,
             "opponent_rd":self.fighter2.rating_deviation,
             "opponent_n_games": len(self.fighter2.games),
             }
        )

        self.fighter2.games.append(
            {"win":winner==2,
             "time":time,
             "current_n_games": len(self.fighter2.games),
             "opponent_rating":self.fighter1.rating,
             "opponent_rd":self.fighter1.rating_deviation,
             "opponent_n_games": len(self.fighter1.games),
             }
        )

    def _check_hps(self):
        if self.fighter1.current_hp <= 0:
            return 2
        elif self.fighter2.current_hp <= 0:
            return 1
        return 0
