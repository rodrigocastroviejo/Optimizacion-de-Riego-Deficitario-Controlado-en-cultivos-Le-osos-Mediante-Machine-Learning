from datetime import datetime, timedelta

print(datetime, type(datetime))
print(timedelta, type(timedelta))

horizon_days = 30
print(datetime.now(), type(datetime.now()))
print((datetime.now() + timedelta(days=horizon_days)), type((datetime.now() + timedelta(days=horizon_days))))

