from glicko_bot.modules.mongo import *
from glicko_bot.modules.pets import Pet
import discord

TABLE_NAME = "pets"

async def create_table():
    if TABLE_NAME not in DB.db.list_collection_names():
        DB.db.create_collection(TABLE_NAME)

async def create_pet_entry(user: discord.Member, pet: Pet) -> None:
    pet.owner_id = user.id
    doc = pet.__dict__
    DB.cursor(TABLE_NAME).insert_one(doc)

async def get_user_pets(user: discord.Member) -> List[dict]:
    return list(DB.cursor(TABLE_NAME).find({"owner_id": user.id}))

async def get_pet(user: discord.Member, pet_id:Optional[int]=None, pet_name:Optional[str]=None) -> Pet:
    filter = {"owner_id": user.id}
    if pet_id is not None:
        filter["id"] = pet_id
    if pet_name is not None:
        filter["name"] = pet_name
    
    val = DB.cursor(TABLE_NAME).find_one(filter)
    if val is not None:
        return Pet.from_dict(val)

async def update_pet_field(user:discord.Member, pet_id:int, field_val:dict) -> None:
    DB.cursor(TABLE_NAME).update_one(
        {"owner_id": user.id, "id": pet_id, "is_alive":True}, 
        {"$set":field_val})
    

async def all_living_pets():
    return list(DB.cursor(TABLE_NAME).find({"is_alive": True}))