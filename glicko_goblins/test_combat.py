import unittest
from combat import Tournament

class TestCombat(unittest.TestCase):
    
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.tourn = Tournament(participants=500, 
                                n_days=50, 
                                daily_combats=250, 
                                daily_mortalities=5
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
    def test_persistence_(self):
        self.tourn.run()
        self.tourn.save(self.path)
        
        loaded_tourn = Tournament.from_save(self.path)
        loaded_tourn.run()


if __name__ == "__main__":
    unittest.main()