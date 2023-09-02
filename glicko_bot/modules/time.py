import pytz
import datetime

uktz = pytz.timezone("Europe/London")

### init time variables ###

#how often to update exchange rates
exchange_update_interval = 5 #minutes

# when tournaments kick off
start_time = [uktz.localize(datetime.time(hour=23)),
              uktz.localize(datetime.time(hour=12, minute=55)),
              uktz.localize(datetime.time(hour=16, minute=30)),
              uktz.localize(datetime.time(hour=19)),
            ]

# when combats happen. Carefully chosen so tournaments don't overlap!
tourn_times = [
               uktz.localize(datetime.time(hour=23, minute=35)),
               uktz.localize(datetime.time(hour=0, minute=5)), # GMT is 1 hour ahead of this
               uktz.localize(datetime.time(hour=0, minute=3)),
               uktz.localize(datetime.time(hour=1, minute=5)),
               uktz.localize(datetime.time(hour=1, minute=35)),
               uktz.localize(datetime.time(hour=2, minute=5)),
    
               uktz.localize(datetime.time(hour=13, minute=30)),
               uktz.localize(datetime.time(hour=14)),
               uktz.localize(datetime.time(hour=14, minute=30)), # GMT is 1 hour ahead of this
               uktz.localize(datetime.time(hour=15)),
               uktz.localize(datetime.time(hour=15, minute=35)),
               uktz.localize(datetime.time(hour=16)),

               uktz.localize(datetime.time(hour=17, minute=5)),
               uktz.localize(datetime.time(hour=17, minute=25)),
               uktz.localize(datetime.time(hour=17, minute=45)), # GMT is 1 hour ahead of this
               uktz.localize(datetime.time(hour=18)),
               uktz.localize(datetime.time(hour=18, minute=15)),
               uktz.localize(datetime.time(hour=18, minute=30)),
    
               uktz.localize(datetime.time(hour=19, minute=35)),
               uktz.localize(datetime.time(hour=20)),
               uktz.localize(datetime.time(hour=20, minute=30)), # GMT is 1 hour ahead of this
               uktz.localize(datetime.time(hour=21)),
               uktz.localize(datetime.time(hour=21, minute=30)),
               uktz.localize(datetime.time(hour=22)),
               ]

# how long the scouting window after tournament start is
scout_duration = 1800

# when to backup the data directory
backup_times = [uktz.localize(datetime.time(hour=i)) for i in range(24) if i%6==0]

# when to add credit to users' wallets
credit_times = [uktz.localize(datetime.time(hour=16, minute=5))]