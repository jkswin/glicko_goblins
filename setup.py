"""
Saving 12 seconds by spending 90 seconds on a script :D
"""

import os
import subprocess
import json

data_path = "glicko_bot/data"
data_stores = {"exchange_history.json": {},
               "exchange.json": {"GLD":0, "SRC":0, "GRC":1},
                "users.json": {}
                }


if __name__ == "__main__":

    subprocess.run("pip install -r requirements.txt")
    if not os.path.exists(data_path):
        print("Creating data directory...")
        os.mkdir(data_path)
        print("Done")
    else:
        print("Data directory already exists.")

    ap = os.path.join(data_path, "art")
    if not os.path.exists(ap):
        os.mkdir(ap)
        
    
    for filename, content in data_stores.items():
        path = os.path.join(data_path, filename)
        if not os.path.exists(path):
            print(f"Creating {path}")
            with open(path, "w") as f:
                json.dump(content, f)
            print("Done")
        else:
            print(f"{path} already exists.")

    print("SETUP COMPLETE!")
