import re
import time
import random
from functools import wraps

def format_runtime(minutes):
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}min"

def calculate_relative_rating(rating, avg_rating):
    return round(rating - avg_rating, 1)

def validate_genre(genre: str) -> bool:
    return bool(re.match(r'^[a-zA-Z\s]+$', genre))

def retry_with_backoff(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_delays = [1, 3, 5]  # seconds
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = retry_delays[attempt]
                time.sleep(delay)
    return wrapper
