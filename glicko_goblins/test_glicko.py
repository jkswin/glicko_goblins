import unittest
import numpy as np

from . import glicko

"""
Verifying that I have correctly implemented the formulas.
Calcs are either examples taken from the paper or done manually with a calculator.
"""

class TestGlicko(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

        self.player1 = {"rating": 1400,
                        "rating_deviation": 80,
                        "game_history":[{"opponent_rating":1500,
                                         "opponent_rd": 350,
                                         "win": 1,
                                         },
                                         {"opponent_rating":1800,
                                         "opponent_rd": 50,
                                         "win": 0,
                                         },
                                         {"opponent_rating":1750,
                                         "opponent_rd": 70,
                                         "win": 1,
                                         },
                                        ]
                        }
        self.player2 = {"rating": 1500,
                        "rating_deviation": 150,
                        "game_history":[{"opponent_rating":1500,
                                         "opponent_rd": 350,
                                         "win": 0,
                                         },
                                         {"opponent_rating":1600,
                                         "opponent_rd": 20,
                                         "win": 0,
                                         },
                                         {"opponent_rating":1300,
                                         "opponent_rd": 260,
                                         "win": 1,
                                         },
                                        ]
                        }
        
        self.player3 = {"rating": 1600,
                        "rating_deviation": 170,
                        "game_history":[{"opponent_rating":1700,
                                         "opponent_rd": 10,
                                         "win": 1,
                                         },
                                         {"opponent_rating":1550,
                                         "opponent_rd": 300,
                                         "win": 1,
                                         },
                                         {"opponent_rating":1600,
                                         "opponent_rd": 300,
                                         "win": 1,
                                         },
                                        ]
                        }
        
        self.player4 = {"rating": 1750,
                        "rating_deviation": 30,
                        "game_history":[{"opponent_rating":1000,
                                         "opponent_rd": 60,
                                         "win": 1,
                                         },
                                         {"opponent_rating":1900,
                                         "opponent_rd": 200,
                                         "win": 0,
                                         },
                                         {"opponent_rating":1500,
                                         "opponent_rd": 350,
                                         "win": 1,
                                         },
                                        ]
                        }

    #@unittest.SkipTest
    def test_game_outcome(self):
        result = glicko.game_outcome(pi_r=self.player1["rating"],
                            pj_r=self.player2["rating"],
                            pi_rd=self.player1["rating_deviation"],
                            pj_rd=self.player2["rating_deviation"])
        
        expected = 0.376
        assert np.round(result, 3) == expected

    #@unittest.SkipTest
    def test_g_rd(self):
        result = glicko.g_rd(rd=self.player3["rating_deviation"])
        expected = 0.88
        assert np.round(result, 2) == expected

     #@unittest.SkipTest
    def test_step1_rd(self):
        """
        Step 1 in the rating update process.
        Compute new rating deviation for a player given constant C.
        C is an estimate  of how much time (in units of rating periods) would need to pass 
        before a rating for a typical player becomes as uncertain as that of an unrated player.
        The RD of an unrated player is 350. 
        """
        c = 63.2
        result = glicko.step1_rd(previous_rd=self.player4["rating_deviation"],
                                 c = c)
        expected = 70.0

        assert np.round(result, 1) == expected

    #@unittest.SkipTest
    def test_expectation_j(self):
        """
        Expectation of the outcome s, given current rating, opponent rating, opponent rating deviation.
        Not to be confused with game_outcome() for a single game which accounts for both 
        player's rating deviations and can be used directly to get expected game outcome.

        For a player, s=1 means a win, s=0 a loss, s=1/2 is a draw.
        """
        result1 = glicko.expectation_j(r=self.player1["rating"], #1400
                                      rj=self.player2["rating"], #1500
                                      rdj=self.player2["rating_deviation"]) #350
        expected1 = 0.37

        result2 = glicko.expectation_j(r=self.player2["rating"], #1500
                                      rj=self.player3["rating"], #1600
                                      rdj=self.player3["rating_deviation"]) #170
        expected2 = 0.38

        assert np.round(result1, 2) == expected1
        assert np.round(result2, 2) == expected2

    #@unittest.SkipTest
    def test_calc_d2(self):
        opponent_rds = []
        opponent_ratings = []
        for opp in self.player1["game_history"]:
            opponent_rds.append(opp["opponent_rd"])
            opponent_ratings.append(opp["opponent_rating"])

        result = glicko.calc_d2(opponent_rds=opponent_rds,
                                opponent_ratings=opponent_ratings,
                                r=self.player1["rating"])
        expected = 103004.5
        assert np.round(result,1) == expected

    #@unittest.SkipTest
    def test_rd_dash(self):

        opponent_rds = []
        opponent_ratings = []
        for opp in self.player1["game_history"]:
            opponent_rds.append(opp["opponent_rd"])
            opponent_ratings.append(opp["opponent_rating"])

        # calced to be ~ 10,000 in previous test
        d2 = glicko.calc_d2(opponent_rds=opponent_rds,
                                opponent_ratings=opponent_ratings,
                                r=self.player1["rating"])
        
        # calced to be ~70 in previous test
        step1_rd = glicko.step1_rd(previous_rd=self.player1["rating_deviation"],
                                   c=63.2)

        result = glicko.rd_dash(rd=step1_rd,
                                d2=d2)
        expected = 97.2
        assert np.round(result, 1) == expected


    @unittest.SkipTest
    def test_r_dash(self):
        raise NotImplementedError()
    
    
    @unittest.SkipTest
    def test_player_update(self):
        raise NotImplementedError()


if __name__ == "__main__":
    unittest.main()
