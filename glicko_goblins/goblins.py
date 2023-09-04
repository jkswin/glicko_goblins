import numpy as np
import scipy.stats as stats
import random
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from .configs import *
from .glicko import game_outcome, MAX_RD, MIN_RD

class Fighter:

    def __init__(self, name=None, entry_day=None, tourn_id=None, tournament_name=None) -> None:
        
        self.name = name
        self.tourn_id = tourn_id
        self.earnings = 0
        self.tournament_name = tournament_name

        # rating metrics
        self.rating: float = 1500.0
        self.rating_deviation: float = 350.0
        self.mean_outcome: float = 0.5
        self.rating_interval: int = None
        self.alive: bool = True

        # __future__
        self.team: str = None
        self.manager: str = None
        self.pep: float = 1
        
        # static stats
        self.max_hp: int = self._truncnorm(*STAT_DISTRIBUTIONS["hp"])
        self.current_hp = self.max_hp
        self.strength: int = self._truncnorm(*STAT_DISTRIBUTIONS["strength"])
        self.cooldown: int = self._truncnorm(*STAT_DISTRIBUTIONS["cooldown"])
        self.lr: float = self._truncnorm(*STAT_DISTRIBUTIONS["lr"])
        self.eagerness: int = np.random.randint(1, MAX_EAGERNESS+1)
        self.funding: int = self._truncnorm(*STAT_DISTRIBUTIONS["funding"])
        

        # action probabilities
        self.guard_prob: float = self._truncnorm(*STAT_DISTRIBUTIONS["guard"])
        self.guardbreak_prob: float = self._generate_guardbreak(self.guard_prob)
        self.parry_prob: float = self._generate_parry(self.cooldown, self.guardbreak_prob)
        self.crit_prob: float = self._generate_crit(self.parry_prob)
        self.dodge_prob: float = self._generate_dodge(self.strength, self.max_hp)

        # multipliers
        self.guts: float = self._generate_guts(self.rating_deviation, self.eagerness)
        self.avarice: float = self._generate_avarice(self.funding, STAT_DISTRIBUTIONS["funding"][3], self.eagerness)
        self.skill: float = 1.0

        # history 
        self.archived_games: list = []
        self.games: list = []
        self.wins: int = 0
        self.total_games: int = 0
        self.entry_day: int = entry_day
        self.time_since_last_combat: int = 0 #days
        self.swings: int = 0
        self.guards_broken: int = 0
        self.successful_guards: int = 0
        self.failed_guards: int = 0
        self.attacks_parried: int = 0
        self.times_parried_by_opponent: int = 0
        self.critical_hits: int = 0
        self.attacks_dodged: int = 0
        self.damage_instances: list = []

    def __str__(self):
        return "\n".join([f"{k.title()}: {v}" for k,v in self.__dict__.items()])

    @staticmethod
    def _truncnorm(mu, std, lb, ub):
        a = (lb-mu)/std
        b = (ub-mu)/std
        val = stats.truncnorm.rvs(a,b,loc=mu,scale=std, size=1)[0]
        if ub >= 1:
            val = int(val)
        return val

    @staticmethod
    def _generate_guardbreak(guard_prob):
        """
        Intuitively thought of as recklessness. 
        Less bothered about guarding = attacking more recklessly.
        """
        return STAT_DISTRIBUTIONS["guard"][3] - guard_prob
    
    @staticmethod
    def _generate_parry(cooldown, guardbreak_prob):
        """
        Opting for no defense maximises your ability to parry and break guards.
        Scaled and normalised by self.cooldown.
        """
        min_cd, max_cd = STAT_DISTRIBUTIONS["cooldown"][2], STAT_DISTRIBUTIONS["cooldown"][3]
        return (max_cd - cooldown) * guardbreak_prob/(max_cd-min_cd)
    
    @staticmethod
    def _generate_crit(parry_prob):
        """
        High parry -> low crit
        """
        return np.clip(0.45 - 2*parry_prob, a_min=0.0001, a_max=0.45)
    
    @staticmethod
    def _generate_dodge(strength, max_hp):
        """
        Depends on HP and Strength. Range between 0 and MAX_DODGE.
        0.5 * (Cos(root_square_sum(HP, Strength)) + 1)
        """
        hp_ceiling, hp_floor = STAT_DISTRIBUTIONS["hp"][3], STAT_DISTRIBUTIONS["hp"][2] 
        strength_ceiling, strength_floor = STAT_DISTRIBUTIONS["strength"][3], STAT_DISTRIBUTIONS["strength"][2] 
        hp_scaler = (2*np.pi)/(hp_ceiling - hp_floor)
        strength_scaler = (2*np.pi)/(strength_ceiling-strength_floor)
        z_hp = max_hp * hp_scaler
        z_strength = strength * strength_scaler
        z = np.sqrt(z_hp**2 + z_strength**2)
        return MAX_DODGE * (0.5 * (np.cos (z+np.pi) + 1))
    
    @staticmethod
    def _generate_guts(rating_deviation, eagerness):
        """
        Adding in some metaawareness. Showing a contestant their rating deviation affects their determination.
        It is also a function of their base eagerness to fight.
        And is realised down the line as a crit chance multiplier based on missing hp.
        """
        return np.mean(
                        (rating_deviation/MAX_RD,
                        eagerness/MAX_EAGERNESS)
                        )
    
    @staticmethod
    def _generate_avarice(funding, max_funding, eagerness):
        """
        Add a sinusoidal damage multiplier based on how much money the goblin is earning.
        Interplays with eagerness to give the idea of "money motivation". 
        I imagine it as some highly paid goblins get cocky, some underpaid underperform and satisfaction fluctuates between the two.
        That also interacts with how generally eager they are.
        """
        av = (MAX_EAGERNESS/eagerness) * (2 * np.pi) * (funding/max_funding)
        return 0.5 * (np.sin(av) + 1)
    
    def _reset(self):
        self.current_hp = self.max_hp
    
    def does_guard(self) -> bool:
        return np.random.uniform(0,1) < self.guard_prob
    
    def does_break(self) -> bool:
        return np.random.uniform(0,1) < self.guardbreak_prob
    
    def does_parry(self) -> bool:
        return np.random.uniform(0,1) < self.parry_prob
    
    def does_crit(self) -> bool:
        """
        As HP decreases, crit chance increases by a factor of the goblin's guts/determinations.
        """
        effective_crit = self.crit_prob + ((1 - self.current_hp/self.max_hp) * self.guts)
        return np.random.uniform(0,1) < effective_crit
    
    def does_dodge(self) -> bool:
        return np.random.uniform(0,1) < self.dodge_prob
    
    def learn_from_experience(self, opponent_rating:int, opponent_rd:int):
        """
        Use Glicko's expected game outcome to scale self.skill by beating opponents against the odds.
        Approximates "learning" from harder games.
        game_outcome() is closer to 1 the more the opponent is expected to win based on rating and rating deviation.
        """
        disparity = game_outcome(self.rating, opponent_rating, self.rating_deviation, opponent_rd)
        self.skill += self.lr * ((2*(disparity - 0.5))**2)
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
        
        if target.does_dodge():
            target.attacks_dodged +=1 
            self.damage_instances.append(0)
            return 
        
        # adjust strength by rust, skill and cooldown. High cooldown implies more body mass to me
        effective_skill = np.max((self.skill - (self.time_since_last_combat * 0.1), 0.8))
        effective_strength = (self.strength + self.cooldown)  * effective_skill
        effective_strength += (effective_strength*self.avarice)
        
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
        if self.total_games > 0:
            return self.wins/self.total_games
        return 0
    
    def winloss(self):
        """
        Calculate win loss ratio.
        """
        if self.total_games > 0:
            wins = self.wins
            losses = self.total_games - self.wins
            if losses > 0:
                wins/=losses
            return wins
        return 0

    ## STR METHODS FOR VIEWING GOBLIN INFO ##
    def describe(self) -> str:
        """Return a natural language description of the goblin."""
    
        return f"Name: {self.name}\nAge: {80-self.max_hp} years\nWeight: {self.cooldown + 10}kg\nMotivation: {self.eagerness} stars\nBench Press: {self.strength}kg\nBrain Cells: {int(self.lr*10e6)}\nWins: {self.wins}\nLosses:{self.total_games - self.wins}\n\n" + self.__scout_report()

    def __scout_report(self):
        """
        Get a language model to describe the Goblin's performance in an opaque manner.
        """
        return ""
    
    def base_stats(self, subset:str="bs") -> dict:
        stats= {"bs":["max_hp", "strength", "cooldown", "eagerness", "lr"],
                "bp": ["guard_prob", "guardbreak_prob", "parry_prob", "crit_prob", "dodge_prob", "guts", "avarice"],
                }
        return {k:v for k,v in self.__dict__.items() if k in stats.get(subset, stats["bs"])}
    
    ## PLOT METHODS FOR VISUALISING GOBLIN INFO ##
    def plot_base_stats(self) -> Figure:
        """
        Plot the Base Stats as a horizontal bar.
        Plot the Base Probabilities as a polygon plot.

        Disclaimer: Quick and dirty.
        """
        bs = self.base_stats(subset="bs")
        bs["hp"] = bs["max_hp"]
        del bs["max_hp"]
        max_vals = {k:STAT_DISTRIBUTIONS.get(k, [None,None,None,None])[3] for k in bs.keys()}
        max_vals.update({"eagerness":MAX_EAGERNESS})
        proportions = {k:v / max_vals[k] for k, v in bs.items()}
        proportions.update({"cooldown": 1 - proportions["cooldown"]}) # greater cooldown is a bad thing so invert
        colours = [plt.cm.RdYlGn(proportions[key]) for key in bs]

        # make fig
        fig, ax = plt.subplots(ncols=2, figsize=(12, 5))
        ax[0].barh(list(proportions.keys()), list(proportions.values()), color=colours)

        #stylise
        ax[0].set_title("Base Stats", size=14)
        ax[0].set_xticks([])
        ytick_labels = [key.title() for key in proportions.keys()]
        ax[0].set_yticks(list(proportions.keys()), ytick_labels)
        ax[0].set_xlim(left=0, right=1)

        # now for the polygon
        ax[1].remove()
        ax_polar = fig.add_subplot(1, 2, 2, projection='polar')
        ax_polar.set_title("Specialisms", size=14)
        bp = self.base_stats("bp")

        # to normalise the polygon, divide by the maximum possible value for each
        fc = self._floors_and_ceilings()
        for k in bp.keys():
            bp[k] /= fc["ceilings"][k]

        sts = list(bp.values())

        angles = np.linspace(0, 2*np.pi, len(bp), endpoint=False)
        ax_polar.fill(angles, sts, alpha=0.4, color="mediumspringgreen")

        ax_polar.set_xticks(angles)
        ax_polar.set_xticklabels([k.replace("_prob", "").title() for k in bp.keys()])
        ax_polar.set_yticklabels([])
        ax_polar.set_xlim(left=0, right=2*np.pi)
        ax_polar.spines['polar'].set_visible(False)

        title = f"{self.name} ({self.tourn_id})"
        plt.subplots_adjust(top=0.75)
        plt.suptitle(title)  

        return fig


    def _floors_and_ceilings(self):
        """Intentionally verbose to show feature interactions directly"""

        return {"floors": {
                        "guard_prob":STAT_DISTRIBUTIONS["guard"][2],
                        "guardbreak_prob":self._generate_guardbreak(STAT_DISTRIBUTIONS["guard"][3]),
                        "parry_prob": self._generate_parry(STAT_DISTRIBUTIONS["cooldown"][3], 
                                                           self._generate_guardbreak(STAT_DISTRIBUTIONS["guard"][3])
                                                           ),
                        "crit_prob": self._generate_crit(self._generate_parry(STAT_DISTRIBUTIONS["cooldown"][2], 
                                                           self._generate_guardbreak(STAT_DISTRIBUTIONS["guard"][2])
                                                           )),
                        "dodge_prob": 0,
                        "guts":self._generate_guts(MIN_RD, 1),
                        "avarice":0,
                        "max_hp": STAT_DISTRIBUTIONS["hp"][2],
                        "hp": STAT_DISTRIBUTIONS["hp"][2],
                        "strength": STAT_DISTRIBUTIONS["strength"][2],
                        "cooldown":STAT_DISTRIBUTIONS["cooldown"][2],
                        "eagerness":1,
                        "lr":STAT_DISTRIBUTIONS["lr"][2],
                        },

                "ceilings": {
                        "guard_prob":STAT_DISTRIBUTIONS["guard"][3],
                        "guardbreak_prob":self._generate_guardbreak(STAT_DISTRIBUTIONS["guard"][2]),
                        "parry_prob":self._generate_parry(STAT_DISTRIBUTIONS["cooldown"][2], 
                                                           self._generate_guardbreak(STAT_DISTRIBUTIONS["guard"][2])
                                                           ),
                        "crit_prob":self._generate_crit(self._generate_parry(STAT_DISTRIBUTIONS["cooldown"][3], 
                                                           self._generate_guardbreak(STAT_DISTRIBUTIONS["guard"][3])
                                                           )),
                        "dodge_prob":MAX_DODGE,
                        "guts":self._generate_guts(MAX_RD, MAX_EAGERNESS),
                        "avarice":1,
                        "max_hp": STAT_DISTRIBUTIONS["hp"][3],
                        "hp": STAT_DISTRIBUTIONS["hp"][3],
                        "strength": STAT_DISTRIBUTIONS["strength"][3],
                        "cooldown": STAT_DISTRIBUTIONS["cooldown"][3],
                        "eagerness":MAX_EAGERNESS,
                        "lr":STAT_DISTRIBUTIONS["lr"][3],
                        },
            }


if __name__ == "__main__":
    g = Fighter()
    print(g.plot_base_stats())
