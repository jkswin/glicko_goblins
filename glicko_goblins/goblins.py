import numpy as np
import scipy.stats as stats
import random
from configs import *


class Fighter:

    def __init__(self, name=None, entry_day=None) -> None:
        
        self.name = name 
        
        # static stats
        self.max_hp: int = self._truncnorm(*STAT_DISTRIBUTIONS["hp"])
        self.current_hp = self.max_hp
        self.strength: int = self._truncnorm(*STAT_DISTRIBUTIONS["strength"])
        self.cooldown: int = self._truncnorm(*STAT_DISTRIBUTIONS["cooldown"])
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
        self.rating_interval: int = None

        # history 
        self.games: list = []
        self.wins: int = 0
        self.total_games: int = 0
        self.entry_day: int = entry_day
        self.time_since_last_combat:int = 0 #days
        self.guards_broken: int = 0
        self.attacks_guarded: int = 0
        self.attacks_parried: int = 0

    def __str__(self):
        return "\n".join([f"{k.title()}: {v}" for k,v in self.__dict__.items()])

    @staticmethod
    def _truncnorm(mu, std, lb, ub):
        a = (lb-mu)/std
        b = (ub-mu)/std
        val = stats.truncnorm.rvs(a,b,loc=mu,scale=std, size=1)[0]
        if ub <= 1:
            return np.round(val, 2)
        return int(val)

    def _generate_guardbreak(self):
        """Intuitively thought of as recklessness. Less bothered about guarding = attacking more recklessly"""
        return np.round(0.9 - self.guard_prob, 2)
    
    def _generate_parry(self):
        """Opting for no defense maximises your ability to parry and break guards"""
        min_cd, max_cd = STAT_DISTRIBUTIONS["cooldown"][2], STAT_DISTRIBUTIONS["cooldown"][3]
        return (max_cd - self.cooldown) * self.guardbreak_prob/(3*(max_cd-min_cd))
    
    def _generate_crit(self):
        return np.clip(0.45 - 2*self.parry_prob, a_min=0.0001, a_max=0.45)
    
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
    
    def swing(self, target):

        effective_strength = np.max((self.strength - self.time_since_last_combat, 
                                     STAT_DISTRIBUTIONS["strength"][2]))
        
        if self.does_crit():
            effective_strength *= 2

        if target.does_parry():
            target.attacks_parried += 1
            self.current_hp -= (1 + target.strength//2)
            return

        if target.does_guard():
            if self.does_break():
                self.guards_broken += 1
                target.current_hp -= (1 + effective_strength//3)
            else:
                target.attacks_guarded +=1
                target.current_hp -= (1 + effective_strength//8)

        else:
            target.current_hp -= (effective_strength//4)
    
    def winrate(self):
        if len(self.games) > 0:
            return self.wins/len(self.games)

        
        
        
if __name__ == "__main__":
    goblin = Fighter()
    print(goblin)