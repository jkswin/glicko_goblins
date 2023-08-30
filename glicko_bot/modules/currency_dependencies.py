"""
The conditions affecting the strength of in-game currencies. 
Based on real-world factors, but no serious ones.
Right now it's rank of a given player (e.g. my amigos) in titles from Riot Games.

RIOT PERSONAL API RATE LIMITS
20 requests every 1 seconds(s)
100 requests every 2 minutes(s)
"""

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
    "GRANDMASTER":  33,
    "CHALLENGER":   33,
}

cfg = dotenv_values(".env")
summoners = json.loads(cfg["SUMMONERS"])

async def fetch_data(session, url):
    async with session.get(url, headers={"X-Riot-Token": cfg["RIOT"]}) as response:
        if response.status == 200:
            return await response.json()
        return []

async def tft_to_currency(session, queue_type, summoner, noise:bool=True):
    summoner_url = f"/lol/summoner/v4/summoners/by-name/{summoner}"
    response = await fetch_data(session, ROUTE + summoner_url)
    
    summoner_id = response.get("id", False)

    if not summoner_id:
        return False

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
    
    if not bool(ranked_info):
        return False
    
    tier = ranked_info["tier"]
    rank = N2I.get(ranked_info["rank"]) 
    lp = ranked_info["leaguePoints"]
    wins = ranked_info["wins"]
    losses = ranked_info["losses"]
    
    return await calculate_currency(tier, rank, lp, wins, losses, noise, session)

async def calculate_currency(tier, rank, lp, wins, losses, noise, session):

    high_elo = ["MASTER", "GRANDMASTER", "CHALLENGER"]
    base_value = 1 + RANK_MULTIPLIERS[tier] - rank
    
    if tier not in high_elo:
        value = base_value + ((4 * lp) / 100)
    else:
        response = await fetch_data(url=ROUTE + f"/tft/league/v1/challenger", session=session)
        if not response:
            return False
        lps = [val["leaguePoints"] for val in response["entries"]]
        average_challenger = np.mean(lps)
        top_player_lp = np.max(lps)
        difference = lp - average_challenger
        value = base_value + (base_value*difference/(top_player_lp + 1))
        
    value *= (wins/losses)**2

    if noise:
        value *= random.uniform(0.9, 1.1)
    
    return np.max((0.0001, value))

async def currency_query(summoners, noise=True):
    async with aiohttp.ClientSession() as session:
        tasks = [tft_to_currency(session, queue_type, summoner, noise=noise) for currency_str, summoner, queue_type in summoners]
        results = await asyncio.gather(*tasks)
        return {summoner[0]: result for summoner, result in zip(summoners, results) if result}
            
