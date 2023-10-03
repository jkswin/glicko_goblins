from glicko_bot.modules.mongo import *
import discord
import datetime

TABLE_NAME = "users"

user_document = {
    "_id": None,
    "wallet": {"GLD":100},
    "exchanges": [],
}

cols = [key for key in user_document.keys()]


async def create_table():
    if TABLE_NAME not in DB.db.list_collection_names():
        DB.db.create_collection(TABLE_NAME)


async def create_user(user: discord.Member) -> None:
    user_data = DB.cursor(TABLE_NAME).find_one({"_id": user.id})
    if user_data is not None:
        return

    doc = user_document.copy()
    doc.update(_id=user.id)
    DB.cursor(TABLE_NAME).insert_one(doc)


async def get_user_data(user: discord.Member) -> Optional[Any]:
    return DB.cursor(TABLE_NAME).find_one({"_id": user.id})

async def get_user_wallet(user: discord.Member) -> Optional[Any]:
    user = await get_user_data(user)
    if user:
        return user.get("wallet",{})
    return {}

async def update_wallet(user: discord.Member, currency: str, amount: Union[float, int] = 0) -> Optional[Any]:
    pipeline = [{"$set": {"wallet." + currency: {"$max": [{"$add": ["$wallet." + currency, amount]}, 0]}}}]

    DB.cursor(TABLE_NAME).update_one(
        {"_id": user.id}, pipeline
    )
    user_data = await get_user_data(user)
    return user_data.get("wallet")

async def get_all_wallets():
    return list(DB.cursor(TABLE_NAME).find({}, {"wallet":1}))

async def reset_user_wallet(user: discord.Member) -> None:
    user_data = await get_user_data(user)
    if user_data is not None:
        wallet_keys = user_data.get("wallet", {}).keys()
        empty_wallet = {k:0 for k in wallet_keys}
        DB.cursor(TABLE_NAME).update_one({"_id": user.id}, {"$set": {"wallet":empty_wallet}})
        user_data = await get_user_data(user)
        return user_data.get("wallet", {})

async def exchange_log(user:discord.Member, to_currency: str, from_currency:str, amount:float, rate:float):
    now = datetime.datetime.now().replace(microsecond=0)

    log = {
        "to_currency":to_currency,
        "from_currency":from_currency,
        "amount":amount,
        "rate": rate,
        "timestamp":now,
    }

    DB.cursor(TABLE_NAME).update_one({"_id": user.id}, {"$push": {"exchanges": log}}, upsert=True)