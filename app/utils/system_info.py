import time

START_TIME = time.time()

def get_uptime() -> float:
    return round(time.time() - START_TIME, 2)