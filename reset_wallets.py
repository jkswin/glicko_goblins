import json
wallet_path = "glicko_bot/data/users.json"

while True:

    user_inp = input("Are you sure you want to reset everybody's wallets?(y/n)")

    if user_inp == "y":
        with open(wallet_path, "r") as f:
            users = json.load(f)
        for user, wallet in users.items():
            for currency, quantity in wallet.items():
                if currency == "GLD":
                    wallet[currency] = 100
                else:
                    wallet[currency] = 0

            users[user] = wallet

        with open(wallet_path, "w") as f:
            json.dump(users, f)
        
        break

    if user_inp == "n":
        break

    else:
        print("That's not an option!")