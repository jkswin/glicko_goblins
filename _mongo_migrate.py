"""
Simple script to port the existing server data I had to mongo
"""


from glicko_bot.modules import mongo, user_funcs, art_funcs, server_funcs, pet_funcs, exchange_funcs
import json 
import os
import asyncio
import random


DATA_PATH = "glicko_bot/data/"
WALLETS = os.path.join(DATA_PATH, "users.json")
TAX = os.path.join(DATA_PATH, "kitty.json")
FOUNDING_COLLECTION = os.path.join(DATA_PATH, "art/founding_collection")
FC_METADATA = os.path.join(FOUNDING_COLLECTION, "metadata.jsonl")

class DummyMember:
    def __init__(self, id) -> None:
        self.id = id

async def main():
    
    await mongo.DB.connect()
    if not mongo.DB.is_connected:
        raise RuntimeError("Database access denied")

    coroutines = [
            user_funcs.create_table(),
            server_funcs.create_table(),
            pet_funcs.create_table(),
            exchange_funcs.create_table(),
            art_funcs.create_table(),
    ]
    await asyncio.gather(*coroutines)

    # migrate wallets
    with open(WALLETS, "r") as f:
        wallets = json.load(f)
    for str_id, contents in wallets.items():
        user = DummyMember(int(str_id))
        await user_funcs.create_user(user)
        for currency, amount in contents.items():
            await user_funcs.update_wallet(user, currency, amount)

    # migrate current tax pool
    with open(TAX, "r") as f:
        tax = json.load(f).get("tax")
    await server_funcs.update_tax(tax)

    # migrate art
    with open(FC_METADATA, "r") as f:
        for line in f:
            line = json.loads(line)
            line["collection"] = "founding_collection"
            line["sale_history"] = []
            line["owner"] = None
            line["for_sale"] = True
            line["base_price"] = random.randint(1000,10000)
            
            await art_funcs.create_art(line)


if __name__ == "__main__":
    asyncio.run(main())