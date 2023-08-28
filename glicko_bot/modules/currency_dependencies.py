"""
The conditions affecting the strength of in-game currencies. 
Based on real-world factors, but no serious ones.
Right now it's rank of a given player (e.g. my amigos) in titles from Riot Games.

RIOT PERSONAL API RATE LIMITS
20 requests every 1 seconds(s)
100 requests every 2 minutes(s)
"""

import requests
import aiohttp
import asyncio
from dotenv import dotenv_values
import json
import numpy as np
import random


ROUTE = "https://euw1.api.riotgames.com"

N2I = {
    "I":    1,
    "II":   2,
    "III":  3,
    "IV":   4,
}

RANK_MULTIPLIERS = {
    "IRON":         4,
    "BRONZE":       9,
    "SILVER":       13,
    "GOLD":         17,
    "PLATINUM":     21,
    "EMERALD":      25,
    "DIAMOND":      29,
    "MASTER":       33,
    "GRANDMASTER":  37,
    "CHALLENGER":   41,
}

cfg = dotenv_values(".env")
summoners = json.loads(cfg["SUMMONERS"])

def soloq_to_currency(summoner_id):
    raise NotImplementedError()
    

cfg = dotenv_values(".env")
summoners = json.loads(cfg["SUMMONERS"])

async def fetch_data(session, url):
    async with session.get(url, headers={"X-Riot-Token": cfg["RIOT"]}) as response:
        return await response.json()

async def tft_to_currency(session, queue_type, summoner):
    summoner_url = f"/lol/summoner/v4/summoners/by-name/{summoner}"
    response = await fetch_data(session, ROUTE + summoner_url)
    
    summoner_id = response["id"]

    if queue_type == "tft":
        ranked_url = f"/tft/league/v1/entries/by-summoner/{summoner_id}"
        response = await fetch_data(session, ROUTE + ranked_url)
        ranked_info = response[0]
    elif queue_type == "lol":
        ranked_url = f"/lol/league/v4/entries/by-summoner/{summoner_id}"
        response = await fetch_data(session, ROUTE + ranked_url)
        ranked_info = [r for r in response if r["queueType"] == "RANKED_SOLO_5x5"][0]

    else:
        raise ValueError("queue_type must be one of ['lol', 'tft']")
    tier = ranked_info["tier"]
    rank = N2I.get(ranked_info["rank"]) 
    lp = ranked_info["leaguePoints"]
    wins = ranked_info["wins"]
    losses = ranked_info["losses"]
    
    return calculate_currency(tier, rank, lp, wins, losses)

def calculate_currency(tier, rank, lp, wins, losses, noise: bool = True):
    high_elo = ["MASTER", "GRANDMASTER", "CHALLENGER"]
    base_value = 1 + RANK_MULTIPLIERS[tier] - rank
    
    if tier not in high_elo:
        value = base_value + ((4 * lp) / 100)
    else:
        mins = []
        maxes = []
        for url_tier in high_elo:
            response = requests.get(ROUTE + f"/tft/league/v1/{url_tier.lower()}",
                                    headers={"X-Riot-Token": cfg["RIOT"]}).json()
            lps = [val["leaguePoints"] for val in response["entries"]]
            mins.append(np.min(lps))
            maxes.append(np.max(lps))
        
        position = high_elo.index(url_tier)
        tier_max = maxes[position]  # maximum of current tier
        
        if url_tier != "CHALLENGER":
            next_tier_min = mins[position + 1]  # minimum of next tier
        else:
            next_tier_min = tier_max
        
        lp_divisor = np.mean((tier_max, next_tier_min))
        value = base_value + ((4*lp)/ lp_divisor)
    
    value *= (wins / losses)/2

    if noise:
        return value * random.uniform(0.98, 1.02)
    
    return value

async def currency_query(summoners, noise=True):
    async with aiohttp.ClientSession() as session:
        tasks = [tft_to_currency(session, queue_type, summoner, noise=noise) for currency_str, summoner, queue_type in summoners]
        results = await asyncio.gather(*tasks)
        return {summoner[0]: result for summoner, result in zip(summoners, results)}
            
