import os
import redis

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
print(redis_url)
r = redis.from_url(redis_url)
print(r.ping())
