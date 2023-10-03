from glicko_bot.modules.mongo import *

TABLE_NAME = "server"

server_document = {
    "tax": 0,
}


cols = [key for key in server_document.keys()]


async def create_table():
    if TABLE_NAME not in DB.db.list_collection_names():
        DB.db.create_collection(TABLE_NAME)
    if DB.cursor(TABLE_NAME).find_one() is None:
        DB.cursor(TABLE_NAME).insert_one(server_document)

async def get_tax():
    result = DB.cursor(TABLE_NAME).find_one()
    return result.get("tax", 0)

async def update_tax(amount: Union[float, int] = 0) -> Optional[Any]:
    pipeline = [{"$set": {"tax": {"$max": [{"$add": ["$tax", amount]}, 0]}}}]

    DB.cursor(TABLE_NAME).update_one(
        {}, pipeline
    )
    return await get_tax()