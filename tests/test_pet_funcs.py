import pytest
import pytest_asyncio
from glicko_bot.modules import mongo, pet_funcs
from glicko_bot.modules.pets import Pet

class DummyUser:
    def __init__(self, id) -> None:
        self.id = id

user1 = DummyUser(123456789)
user2 = DummyUser(987654321)
user3 = DummyUser(192837465)


@pytest_asyncio.fixture
async def db_connect():
    await mongo.DB.connect()
    if not mongo.DB.is_connected:
        raise RuntimeError("Database access denied")
    else:
        print("Connected!")

    await pet_funcs.create_table()

@pytest.mark.usefixtures("db_connect")
@pytest.mark.asyncio
async def test_entry_and_get():
    pets_user1=await pet_funcs.get_user_pets(user1)
    pets_user2=await pet_funcs.get_user_pets(user2)
    pets_user3=await pet_funcs.get_user_pets(user3)

    pet1 = Pet()
    pet1.id = len(pets_user1) + 1
    pet2 = Pet()
    pet2.id = len(pets_user2) + 1
    pet3 = Pet()
    pet3.id = len(pets_user3) + 1


    await pet_funcs.create_pet_entry(user1, pet1)
    await pet_funcs.create_pet_entry(user2, pet2)
    await pet_funcs.create_pet_entry(user3, pet3)
    pet1.owner_id = user1.id
    pet2.owner_id = user2.id
    pet3.owner_id = user3.id
    
    returned_pet1 = await pet_funcs.get_pet(user1, pet_id=pet1.id)
    returned_pet2 = await pet_funcs.get_pet(user2, pet_id=pet2.id)
    returned_pet3 = await pet_funcs.get_pet(user3, pet_id=pet3.id)

    await pet_funcs.update_pet_field(user1, pet1.id, {"is_alive":False,"n_deaths":1})
    updated_pet = await pet_funcs.get_pet(user1, pet1.id)

    all_pets = await pet_funcs.all_living_pets()

    mongo.DB.drop("pets")

    for key in pet1.__dict__.keys():
        assert pet1.__dict__[key] == returned_pet1.__dict__[key]
        assert pet2.__dict__[key] == returned_pet2.__dict__[key]
        assert pet3.__dict__[key] == returned_pet3.__dict__[key]

    
    assert len(all_pets) == 2
    assert updated_pet.is_alive == False
    assert updated_pet.n_deaths == 1

    