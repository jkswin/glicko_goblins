import numpy as np
import scipy.stats as stats
import random
from configs import *
from glicko import game_outcome

class Fighter:

    def __init__(self, name=None, entry_day=None) -> None:
        
        self.name = name 
        
        # static stats
        self.max_hp: int = self._truncnorm(*STAT_DISTRIBUTIONS["hp"])
        self.current_hp = self.max_hp
        self.strength: int = self._truncnorm(*STAT_DISTRIBUTIONS["strength"])
        self.cooldown: int = self._truncnorm(*STAT_DISTRIBUTIONS["cooldown"])
        self.lr: float = self._truncnorm(*STAT_DISTRIBUTIONS["lr"])
        self.eagerness: int = random.choice([1,2,3])
        self.alive: bool = True

        # action probabilities
        self.guard_prob: float = self._truncnorm(*STAT_DISTRIBUTIONS["guard"])
        self.guardbreak_prob: float = self._generate_guardbreak()
        self.parry_prob: float = self._generate_parry()
        self.crit_prob: float = self._generate_crit()
        

        # rating metrics
        self.rating: int = 1500
        self.rating_deviation: int = 350
        self.mean_outcome: float = 0.5
        self.rating_interval: int = None

        # history 
        self.games: list = []
        self.wins: int = 0
        self.total_games: int = 0
        self.entry_day: int = entry_day
        self.time_since_last_combat:int = 0 #days
        self.swings: int = 0
        self.guards_broken: int = 0
        self.successful_guards: int = 0
        self.failed_guards: int = 0
        self.attacks_parried: int = 0
        self.times_parried_by_opponent: int = 0
        self.critical_hits: int = 0
        self.damage_instances: list = []
        self.skill: int = 1

        # __future__
        self.team: str = None
        self.manager: str = None
        
    def __str__(self):
        return "\n".join([f"{k.title()}: {v}" for k,v in self.__dict__.items()])

    @staticmethod
    def _truncnorm(mu, std, lb, ub):
        a = (lb-mu)/std
        b = (ub-mu)/std
        val = stats.truncnorm.rvs(a,b,loc=mu,scale=std, size=1)[0]
        if ub <= 1:
            return np.round(val, 5)
        return int(val)

    def _generate_guardbreak(self):
        """
        Intuitively thought of as recklessness. 
        Less bothered about guarding = attacking more recklessly.
        """
        return np.round(STAT_DISTRIBUTIONS["guard"][3] - self.guard_prob, 2)
    
    def _generate_parry(self):
        """
        Opting for no defense maximises your ability to parry and break guards.
        Scaled and normalised by self.cooldown.
        """
        min_cd, max_cd = STAT_DISTRIBUTIONS["cooldown"][2], STAT_DISTRIBUTIONS["cooldown"][3]
        return (max_cd - self.cooldown) * self.guardbreak_prob/(3*(max_cd-min_cd))
    
    def _generate_crit(self):
        return np.clip(0.45 - 2*self.parry_prob, a_min=0.0001, a_max=0.45)
    
    def _generate_lr(self):
        return 
    
    def _reset(self):
        self.current_hp = self.max_hp
    
    def does_guard(self) -> bool:
        return np.random.uniform(0,1) < self.guard_prob
    
    def does_break(self) -> bool:
        return np.random.uniform(0,1) < self.guardbreak_prob
    
    def does_parry(self) -> bool:
        return np.random.uniform(0,1) < self.parry_prob
    
    def does_crit(self) -> bool:
        return np.random.uniform(0,1) < self.crit_prob
    
    def learn_from_experience(self, opponent_rating:int, opponent_rd:int):
        """
        Use Glicko's expected game outcome to scale self.skill by beating opponents against the odds.
        Approximates "learning" from harder games.
        game_outcome() is closer to 1 the more the opponent is expected to win based on rating and rating deviation.

        """
        disparity = self.lr * (game_outcome(self.rating, opponent_rating, self.rating_deviation, opponent_rd) - 0.5) 
        self.skill += disparity
        self.skill = np.clip(self.skill, a_min=1, a_max=10)

    
    def swing(self, target):
        """
        Action logic for a Goblin. A goblin swings every self.cooldown iterations of combat.
        """
        self.swings += 1

        # check for self damage
        if target.does_parry():
            op_damage = int(1 + target.strength * COMBAT_MULTIPLIERS["parry"])
            self.current_hp -= op_damage

            target.attacks_parried += 1
            target.damage_instances.append(op_damage)
            self.times_parried_by_opponent += 1
            return
        
        # adjust strength by rust and skill
        effective_skill = np.max((self.skill - (self.time_since_last_combat * 0.1), 0.8))
        effective_strength = self.strength  * effective_skill
        
        if self.does_crit():
            self.critical_hits += 1
            effective_strength *= COMBAT_MULTIPLIERS["crit"]

        # action logic
        if target.does_guard():
            if self.does_break():
                self.guards_broken += 1
                target.failed_guards +=1 
                damage = 1 + effective_strength * COMBAT_MULTIPLIERS["guardbreak"]
                
            else:
                target.successful_guards +=1
                damage = 1 + effective_strength * COMBAT_MULTIPLIERS["guard"]

        else:
            damage = 1 + effective_strength * COMBAT_MULTIPLIERS["vanilla"]

        # multiply by random float between 0.9 and 1
        damage = int(damage * np.random.uniform(0.9, 1, 1)[0])
        target.current_hp -= damage
        self.damage_instances.append(damage)
    
    def winrate(self):
        """
        Calculate winrate.
        """
        if len(self.games) > 0:
            return self.wins/len(self.games)

    def describe(self) -> str:
        """Return a natural language description of the goblin."""
    
        return f"Name: {self.name}\nAge: {80-self.max_hp} years\nWeight: {self.cooldown + 10}kg\nMotivation: {self.eagerness} stars\nBench Press: {self.strength}kg\nBrain Cells: {int(self.lr*10e6)}\nWins: {self.wins}\nLosses:{self.total_games - self.wins}\n\n" + self.__scout_report()

    def __scout_report(self):
        """
        Get a language model to describe the Goblin's performance in an opaque manner.
        """
        return ""
    
    def polygon(self):
        raise NotImplementedError("WIP")
        
if __name__ == "__main__":
    goblin = Fighter(name="TestGoblin56")
    print(goblin.describe())