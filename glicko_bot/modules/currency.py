#https://realpython.com/async-io-python/
"""
RIOT PERSONAL API RATE LIMITS
20 requests every 1 seconds(s)
100 requests every 2 minutes(s)
"""

import aiohttp
import asyncio
from dotenv import dotenv_values
import json
import numpy as np
from abc import ABC, abstractmethod
import warnings
import pandas as pd
from datetime import datetime

class Coin:
    """
    Abstract coin class that depends on some API for calculating value.
    """
    def __init__(self, session: aiohttp.ClientSession, name: str = None, noise:bool=True):
        self.session = session
        self.name = name
        self.headers = {}
        self.fetches = 0
        self.noise = noise
        self.cfg = dotenv_values(".env") # grant the coin access to api keys
    
    async def fetch_data(self, url: str) -> dict:
            async with self.session.get(url, headers=self.headers) as response:
                self.fetches += 1
                return await response.json()

    @staticmethod      
    def subtract(a,b):
        """
        Subtract a from b without going below 0.
        """
        return max([b-a, 0])
    
    @staticmethod
    def gaussian_noise(value):
        return np.random.normal(
            loc=1,
            scale=0.02
        ) * value
    
    
    @abstractmethod
    def value(self):
        pass
            
class RiotCoin(Coin):
    def __init__(self, session: aiohttp.ClientSession, name:str, summoner:str, queue_type:str, noise:bool=True):
        super().__init__(session, name, noise)
        self.route = "https://euw1.api.riotgames.com"
        self.n2i = {
                    "I":    1,
                    "II":   2,
                    "III":  3,
                    "IV":   4,
                }
        self.rank_multipliers = {
                    "IRON":         4,
                    "BRONZE":       9,
                    "SILVER":       13,
                    "GOLD":         17,
                    "PLATINUM":     21,
                    "EMERALD":      25,
                    "DIAMOND":      29,
                    "MASTER":       33,
                    "GRANDMASTER":  33,
                    "CHALLENGER":   33,
                }
        self.queue_types = ["lol", "tft"]
        self.header_options = {"lol":{"X-Riot-Token": self.cfg["RIOT_LOL_TOKEN"]},
                                "tft":{"X-Riot-Token": self.cfg["RIOT_TFT_TOKEN"]},
                                }

        self.summoner = summoner
        self.queue_type = queue_type
        self.headers = self.header_options.get(self.queue_type, {})

        
    async def value(self) -> float or False:
        """
        Parse the summoner name and queue_type to return the value of the coin.
        """
        summoner_id = await self._retrieve_summoner_id()
        if not summoner_id:
            warnings.warn(f"A summoner ID was not returned for {self.summoner}.\nCheck that {self.summoner} is a valid summoner name!")
            return False
        
        if self.queue_type == "tft":
            ranked_url = self.route + f"/tft/league/v1/entries/by-summoner/{summoner_id}"
            response = await self.fetch_data(ranked_url)
            ranked_info = DefaultList(response)[0]

        elif self.queue_type == "lol":
            ranked_info = False
            ranked_url = self.route + f"/lol/league/v4/entries/by-summoner/{summoner_id}"
            response = await self.fetch_data(ranked_url)
            for val in response:
                if val.get("queueType", "") == "RANKED_SOLO_5x5":
                    ranked_info = val
                    break
        else:
            raise ValueError(f"queue_type must be one of {self.queue_types}")
        
        if not ranked_info:
            warnings.warn(f"There is currently no {self.queue_type} ranked information for {self.summoner}.")
            return ranked_info

        return await self._calculate_value(
            tier = ranked_info["tier"],
            rank = self.n2i.get(ranked_info["rank"]),
            lp = ranked_info["leaguePoints"],
            wins = ranked_info["wins"],
            losses = ranked_info["losses"],
        )
    
    async def _calculate_value(self, tier, rank, lp, wins, losses) -> float or False:
        """
        Calculate a currency value from performance metrics.
        """
        high_elo = ["MASTER", "GRANDMASTER", "CHALLENGER"]
        challenger_league_endpoint = "/tft/league/v1/challenger"
        base_value = 1 + self.rank_multipliers[tier] - rank
        if tier not in high_elo:
            value = base_value + ((4 * lp) / 100)
        else:
            response = await self.fetch_data(self.route + challenger_league_endpoint)
            if not response:
                warnings.warn(f"Could not retrieve data from {challenger_league_endpoint}")
                return False
            lps = [val.get("leaguePoints", 1) for val in response["entries"]]
            average_challenger = np.mean(lps)
            top_player_lp = np.max(lps)
            difference = self.subtract(average_challenger, lp)
            value = base_value + (base_value*difference/(top_player_lp + 1))

        if self.noise:
            value = self.gaussian_noise(value)
        return value * self.wl_ratio2(wins, losses)

    async def _retrieve_summoner_id(self):
        summoner_url = self.route + f"/lol/summoner/v4/summoners/by-name/{self.summoner}"
        response = await self.fetch_data(summoner_url)
        return response.get("id", False)
    
    @staticmethod
    def wl_ratio2(wins, losses):
        """
        Define pseudo-ratio that is not undefined in the event of 0s.
        """
        if not wins:
            wins = 1
        if losses:
            return (wins/losses)**2      
        return wins**2

class AirCoin(Coin):
    def __init__(self, session: aiohttp.ClientSession, name:str, latitude: str, longitude: str, noise:bool=True):
        super().__init__(session, name, noise)
        self.route = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={latitude}&longitude={longitude}&hourly=pm10&timezone=Europe%2FLondon"

    async def value(self):
        response = await self.fetch_data(self.route)
        data = response.get("hourly", None)
        if data is None:
            warnings.warn(f"Failed to get air quality value from {self.route}")
            return 0
        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"])
        current_time = datetime.now().time()
        current_time_timestamp = pd.Timestamp(datetime.combine(pd.Timestamp.now().date(), current_time))
        # Find the closest row to the current time
        closest_row = df.iloc[(df['time'] - current_time_timestamp).abs().idxmin()]
        value = closest_row["pm10"]
        if self.noise:
            value = self.gaussian_noise(value)
        return value


class CoinBag(Coin):
    """
    Mean pooling of multiple coin instances.
    """
    def __init__(self, session, name:str, coins=None, noise:bool=True) -> None:
        super().__init__(session, name, noise)
        self.coins = []
        if coins is not None:
            self.add_coins(coins)
        self.name = name

    def add_coin(self, coin:Coin):
        if isinstance(coin, Coin):
            self.coins.append(coin)

        elif isinstance(coin, dict):
            coin_type = COIN_FROM_TYPE[coin["coin_type"]]
            coin = coin_type(self.session, **coin["meta"])
            self.coins.append(coin)

        else:
            raise ValueError("Only instances of Coin can be added to the bag.")
        
    def add_coins(self, coins:list[Coin]):
        [self.add_coin(c) for c in coins]
    
    async def value(self):
        return np.mean([await coin.value() for coin in self.coins])
    

class DefaultList(list):
    def __init__(self, data=None, default_value=False):
        super().__init__(data or [])
        self.default_value = default_value

    def __getitem__(self, index):
        if index < 0:
            raise IndexError("Negative indices are not supported")
        try:
            return super().__getitem__(index)
        except IndexError:
            return self.default_value
        
def coin_configs_are_valid(cfgs:list):
    if not isinstance(cfgs, list):
        raise TypeError("cfgs should be a list")
    
    for item in cfgs:
        if not isinstance(item, dict):
            raise TypeError("All items in cfgs list must be type 'dict'")
        
        if list(item.keys()) != ["coin_type", "meta"]:
            raise ValueError("Each dict in cfgs should have only the 'coin_type' and 'meta' keys.")
        
        if (type(item["coin_type"]) != str) or (item["coin_type"] not in COINTYPES):
            raise TypeError(f"coin_type must be one of {COINTYPES}")
        
        if item["coin_type"] == "bag":
            coin_configs_are_valid(item["meta"]["coins"])

    return True


# new coin configs rather than having it in .env:
example_coin_config = [{"coin_type": "riot",
                        "meta": {"name": "BAB",
                                 "summoner":"thebausffs",
                                 "queue_type":"lol"}},

                       {"coin_type": "riot",
                        "meta": {"name": "DRT",
                                 "summoner":"drututt",
                                 "queue_type":"lol"}},

                        {"coin_type": "riot",
                         "meta": {"name": "WET",
                                  "summoner":"Wet Jungler",
                                  "queue_type":"tft"}},

                        {"coin_type": "air",
                         "meta": {"name": "ULN",
                                  "latitude":"47.91",
                                  "longitude":"106.88"}},

                        {"coin_type": "bag",
                         "meta": {"name":"GRP",
                                  "coins": [{"coin_type": "riot",
                                            "meta": {"name": "WET",
                                                     "summoner":"Wet Jungler",
                                                     "queue_type":"tft"
                                                    }},
                                            {"coin_type": "air",
                                            "meta": {"name": "ULN",
                                                     "latitude":"47.91",
                                                     "longitude":"106.88"}},
                                            ]}}
                       ]

COIN_FROM_TYPE = {
    "riot": RiotCoin,
    "air": AirCoin,
    "bag": CoinBag,
}

COINTYPES = ["riot", "air", "bag"]

async def currency_query(config_path):
    output = {}
    with open(config_path, "r") as f:
        cfg = [json.loads(line) for line in f]

    async with aiohttp.ClientSession() as session:
        if coin_configs_are_valid(cfg):
            for coin in cfg:
                coin_type = COIN_FROM_TYPE[coin["coin_type"]]
                coin = coin_type(session, **coin["meta"])
                val = await coin.value()
                if not val:
                    val = 1
                output[coin.name] = val
                await asyncio.sleep(0.5)
    return output
