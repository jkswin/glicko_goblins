import datetime

tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

### init time variables ###

#how often to update exchange rates
exchange_update_interval = 5 #minutes

# when tournaments kick off
start_time = [datetime.time(hour=23, minute=15, tzinfo=tz),
              datetime.time(hour=12, minute=55, tzinfo=tz),
              datetime.time(hour=16, minute=30, tzinfo=tz),
              datetime.time(hour=19, tzinfo=tz),
            ]

# when combats happen. Carefully chosen so tournaments don't overlap!
tourn_times = [
               datetime.time(hour=23, minute=50, tzinfo=tz),
               datetime.time(hour=0, minute=5, tzinfo=tz), # GMT is 1 hour ahead of this
               datetime.time(hour=0, minute=30, tzinfo=tz),
               datetime.time(hour=1, minute=5, tzinfo=tz),
               datetime.time(hour=1, minute=35, tzinfo=tz),
               datetime.time(hour=2, minute=5, tzinfo=tz),
    
               datetime.time(hour=13, minute=30, tzinfo=tz),
               datetime.time(hour=14, tzinfo=tz),
               datetime.time(hour=14, minute=30, tzinfo=tz), # GMT is 1 hour ahead of this
               datetime.time(hour=15, tzinfo=tz),
               datetime.time(hour=15, minute=35, tzinfo=tz),
               datetime.time(hour=16, tzinfo=tz),

               datetime.time(hour=17, minute=5, tzinfo=tz),
               datetime.time(hour=17, minute=25, tzinfo=tz),
               datetime.time(hour=17, minute=45, tzinfo=tz), # GMT is 1 hour ahead of this
               datetime.time(hour=18, tzinfo=tz),
               datetime.time(hour=18, minute=15, tzinfo=tz),
               datetime.time(hour=18, minute=30, tzinfo=tz),
    
               datetime.time(hour=19, minute=35, tzinfo=tz),
               datetime.time(hour=20, tzinfo=tz),
               datetime.time(hour=20, minute=30, tzinfo=tz), # GMT is 1 hour ahead of this
               datetime.time(hour=21, tzinfo=tz),
               datetime.time(hour=21, minute=30, tzinfo=tz),
               datetime.time(hour=22, tzinfo=tz),
               ]

# how long the scouting window after tournament start is
scout_duration = 1800

# when to backup the data directory
backup_times = [datetime.time(hour=i, tzinfo=tz) for i in range(24) if i%6==0]

# when to add credit to users' wallets
credit_times = [datetime.time(hour=16, minute=5, tzinfo=tz)]