from glicko_bot.modules.mongo import *
import discord
from pymongo import ReturnDocument

# TODO: add art document/create art listing
# TODO: weekly collection that uses text-to-image model to create N images based on XYZ

TABLE_NAME = "art"

art_document = {"name": None, 
                "base_price": 1, 
                "path": None, 
                "owner": None, 
                "uid": None, 
                "for_sale": True, 
                "sale_history": [], #{"from": "", "to": "example_person", "price": 750, "timestamp":datetime}
                "collection":None
                }

cols = [key for key in art_document.keys()]

async def create_table():
    if TABLE_NAME not in DB.db.list_collection_names():
        DB.db.create_collection(TABLE_NAME)

async def create_art(art:dict) -> None:
    art_data = DB.cursor(TABLE_NAME).find_one({"uid": art["uid"]})
    if art_data is not None:
        return
    DB.cursor(TABLE_NAME).insert_one(art)

async def list_stock():
    return list(DB.cursor(TABLE_NAME).find({"for_sale":True}))

async def get_art(uid, for_sale:bool=True):
    return DB.cursor(TABLE_NAME).find_one({"uid":uid, "for_sale":for_sale})

async def change_hands(uid:int, owner:discord.Member or None, buyer:discord.Member, sale_price:float):
    
    sale_log = {"from_id":None, "to_id": buyer.id, "from_name": None, "to_name":buyer.name, "sale_price": sale_price}
    if owner is not None:
        sale_log.update({"from_id":owner.id, "from_name":owner.name})
    pipeline = [
        {
            "$set": {
                "owner": buyer.id,
                "for_sale": False,
            }
        },
        {
            "$push": {
                "sale_history": sale_log,
            }
        }
    ]
    DB.cursor(TABLE_NAME).find_one_and_update({"uid":uid},
                                              pipeline)
    

async def list_art(user:discord.Member, uid:int, new_price:float):
    return DB.cursor(TABLE_NAME).find_one_and_update({"owner":user.id, "uid":uid},
                                              {
            "$set": {
                "for_sale": True,
                "base_price": new_price,
            }
        },
        return_document=ReturnDocument.BEFORE)

async def show_off(user:discord.Member):
    return list(DB.cursor(TABLE_NAME).find({"owner":user.id}))
    