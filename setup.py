"""
Saving 12 seconds by spending 90 seconds on a script :D
"""

import os
import subprocess
import json
import warnings


data_path = "glicko_bot/data"
backup_path = "glicko_bot/backup"
tourn_archive_path = "glicko_bot/data/archive"

data_stores = {"exchange_history.json": {},
               "exchange.json": {"GLD":1},
                "users.json": {},
                "kitty.json": {"tax":100},
                "pets.json":{},
                }


if __name__ == "__main__":
    
    # try install dependencies with pip
    try:
        subprocess.run(["pip", "install", "-r", "requirements.txt"])
    except Exception as e:
        print(e)
        print("Requirements will need installing manually.")

    # try create .env file
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("DISCORD=YOUR_API_KEY\nRIOT=YOUR_API_KEY\nSUMMONERS=[[`GRC`, `RandomExampleName`, `tft`], ['SRC', `OtherExample`, `lol`]]")
        warnings.warn("Add the appropriate API keys and Summoners to the newly created .env file.\n")
        
    # try create data directory
    if not os.path.exists(data_path):
        print("Creating data directory...")
        os.mkdir(data_path)
        print("Done")
    else:
        print(f"{data_path} already exists.")

    # try create archive directory
    if not os.path.exists(tourn_archive_path):
        print("Creating archive directory...")
        os.mkdir(tourn_archive_path)
        print("Done")
    else:
        print(f"{data_path} already exists.")

    # try create backup directory
    if not os.path.exists(backup_path):
        print("Creating backup directory...")
        os.mkdir(backup_path)
        print("Done")
    else:
        print(f"{backup_path} already exists.")

    # try create artwork folder
    ap = os.path.join(data_path, "art")
    if not os.path.exists(ap):
        os.mkdir(ap)
        first_collection_path = os.path.join(ap, "founding_collection")
        os.mkdir(first_collection_path)
        with open(os.path.join(first_collection_path, "metadata.jsonl"), "w") as f:
            json.dump({"name": "EXAMPLE", "base_price": 100, "path": "EXAMPLE.png", "owner": "", "uid": 1, "for_sale": 1, "sale_history": []}, f)
            f.write("\n")
        print(f"Succesfully created {first_collection_path}! Time to add art and metadata!")
    else:
        print(f"{ap} already exists!")

    
    # try add fundamental data stores to data path
    for filename, content in data_stores.items():
        path = os.path.join(data_path, filename)
        if not os.path.exists(path):
            print(f"Creating {path}")
            with open(path, "w") as f:
                if filename.endswith(".json"):
                    json.dump(content, f)
                else:
                    f.write(content)
            print("Done")
        else:
            print(f"{path} already exists.")

    print("SETUP COMPLETE!")
