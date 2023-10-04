from glicko_bot.modules.mongo import *
import datetime
import pymongo

__all__ = [
    "create_table",
    "update_exchange_rate",
    "get_current_rate",
    "get_last_n_weeks",
]

TABLE_NAME = "exchange"

exchange_document = {
   "timestamp":None,
   "currencies":{}, #{"GLD":1}
}

cols = [key for key in exchange_document.keys()]


async def create_table():
    if TABLE_NAME not in DB.db.list_collection_names():
        DB.db.create_collection(TABLE_NAME)
        DB.cursor(TABLE_NAME).insert_one({
        "timestamp": datetime.datetime.now(),
        "currencies":{"GLD":1},
    })


async def update_exchange_rate(rates):
    current = await get_current_rate()
    if current is None:
        current = {}
    else:
        current = current.get("currencies", {})
        current.update(rates)
    exchange_rate_entry = {
        "timestamp": datetime.datetime.now(),
        "currencies":current,
    }
    DB.cursor(TABLE_NAME).insert_one(exchange_rate_entry)


async def get_current_rate():
  return DB.cursor(TABLE_NAME).find_one(sort=[("timestamp", pymongo.DESCENDING)])


async def get_last_n_days(days:int=7):
    days_ago = datetime.datetime.now() - datetime.timedelta(days=days)
    return list(DB.cursor(TABLE_NAME).find({"timestamp": {"$gte": days_ago}}))