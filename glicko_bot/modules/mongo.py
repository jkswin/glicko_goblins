# inspiration for mongo migration 
# https://github.com/Modern-Realm/economy-bot-discord.py/tree/master/economy%20with%20mongoDB

# use @commands.guild_only decorator on all commands

# Current data directory - glicko_goblins/glicko_bot/data/
# Contains:
#          - exchange_history.json {"datetime_str": {"coin": "rate", "coin": "rate"}}
#          - exchange.json {"coin": "rate", "coin": "rate"} combine these two by just taking most recent?^
#          - kitty.json {"tax": float}

#          - users.json {"discord_user_id": {"coin": quantity, "coin": quantity}}
#          - pets.json {"discord_user_id": [{pet_dict}, {pet_dict}]}

#          - Make Transaction object that always processes tax? to monitor when people move money. Also add to exchange_history
#            !exchange 100 GLD ABC 

#          art/
#                founding_collection/
#                                       - .pngs
#                                       - metadata.jsonl line> {"name": "Lemons", "base_price": 288931.0, "path": "lemons.png", "owner": "joe", "uid": 1, "for_sale": 1, "sale_history": [{"from": "", "to": "joe", "price": 750}]}

# USER-DATA : owned_pets, wallets
# SERVER-DATA : exchange rates, tax, artwork

# lets have a 'users' table and a 'server' table
# users: {"_id":1,
#         "discord_user_id":12345,
#         "wallet": {"GLD": 3, "ABC": 12},
#         "pets": {}
#
#
#
#
#
#
#
#
#

from config import Auth
from typing import Mapping, Any, Optional, Union, List
from pymongo import MongoClient, errors
from pymongo.database import Database as MongoDB
from pymongo.collection import Collection

class DataBase:
    def __init__(self):
        self.cluster: Optional[MongoClient[Mapping[str, Any]]] = None
        self.db: Optional[MongoDB[Mapping[str, Any]]] = None

    async def connect(self):
        try:
            self.cluster = MongoClient(Auth.CLUSTER_AUTH_URL)
            self.db = self.cluster[Auth.DB_NAME]
        except errors.OperationFailure:
            self.cluster = None
        return self

    @property
    def is_connected(self) -> bool:
        return self.cluster is not None

    def cursor(self, table_name: str) -> Collection[Mapping[str, Any]]:
        return self.db[table_name]
    
    def drop(self, table_name:str):
        self.db.drop_collection(table_name)


DB = DataBase()
    