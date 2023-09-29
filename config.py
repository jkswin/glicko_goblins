from os import getenv
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(raise_error_if_not_found=True))


class Auth:
    # discord api
    DISCORD_TOKEN = getenv("DISCORD_TOKEN")
    COMMAND_PREFIX = getenv("COMMAND_PREFIX")

    # riot api
    RIOT_LOL_TOKEN = getenv("RIOT_LOL_TOKEN")
    RIOT_TFT_TOKEN = getenv("RIOT_TFT_TOKEN")
    
    # nlp apis
    HF_TOKEN = getenv("HF_TOKEN")
    OPENAI_TOKEN = getenv("OPENAI_TOKEN")

    # mongodb api
    CLUSTER_AUTH_URL = getenv("CLUSTER_AUTH_URL")
    DB_NAME = getenv("DB_NAME")
