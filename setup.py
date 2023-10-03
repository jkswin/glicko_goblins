"""
Saving 12 seconds by spending 90 seconds on a script :D
"""

import os
import json
import warnings
from config import Auth


data_path = "glicko_bot/data"

coin_config_path = "coin.cfg"
example_coin_config = [{"coin_type": "riot",
                        "meta": {"name": "BAB",
                                 "summoner":"thebausffs",
                                 "queue_type":"lol"}},

                       {"coin_type": "riot",
                        "meta": {"name": "DRT",
                                 "summoner":"drututt",
                                 "queue_type":"lol"}},

                        {"coin_type": "riot",
                         "meta": {"name": "WET",
                                  "summoner":"Wet Jungler",
                                  "queue_type":"tft"}},

                        {"coin_type": "air",
                         "meta": {"name": "ULN",
                                  "latitude":"47.91",
                                  "longitude":"106.88"}},

                        {"coin_type": "bag",
                         "meta": {"name":"GRP",
                                  "coins": [{"coin_type": "riot",
                                            "meta": {"name": "WET",
                                                     "summoner":"Wet Jungler",
                                                     "queue_type":"tft"
                                                    }},
                                            {"coin_type": "air",
                                            "meta": {"name": "ULN",
                                                     "latitude":"47.91",
                                                     "longitude":"106.88"}},
                                            ]}}
                       ]


if __name__ == "__main__":

    # try create .env file
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            for secret in Auth.__dict__.keys():
                f.write(f"{secret}=\n")
        warnings.warn("Add the appropriate API keys to the newly created .env file.\n")
        
    # try create data directory
    if not os.path.exists(data_path):
        print("Creating data directory...")
        os.mkdir(data_path)
        print("Done")
    else:
        print(f"{data_path} already exists.")

    # try create base coin config
    if not os.path.exists(coin_config_path):
        print("Creating example coin configs...")
        with open(coin_config_path, "w") as f:
            for line in example_coin_config:
                json.dump(line,f)
                f.write("\n")
        print("Done")

    # try create artwork folder
    ap = os.path.join(data_path, "art")
    if not os.path.exists(ap):
        os.mkdir(ap)
        print(f"Succesfully created {ap}! Time to add art and metadata!")
    else:
        print(f"{ap} already exists!")


    print("SETUP COMPLETE!")
