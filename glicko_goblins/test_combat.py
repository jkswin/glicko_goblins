import unittest
from .combat import Tournament

class TestCombat(unittest.TestCase):
    
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.tourn = Tournament(participants=700, 
                                n_days=75,
                                daily_combats=500, 
                                daily_mortalities=0,
                                )
        self.path = "glicko_goblins/data/tournament.pkl"
    
    #@unittest.SkipTest
    def test_hat_draw(self):
        draw = self.tourn.hat_draw()
        # check every player has an opponent
        assert len(draw) == 2 * self.tourn.daily_combats
        for a,b in zip(draw[::2], draw[1::2]):
            assert a != b
    
    #@unittest.SkipTest
    def test_run(self):
        self.tourn.run()


if __name__ == "__main__":
    unittest.main()