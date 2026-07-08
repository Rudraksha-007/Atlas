import os
import redis
from os import getenv
from functools import lru_cache
import json, uuid

from typing import Tuple, Optional


class Redis_service:
    QUEUE_KEY = "capsule:delivery_queue"
    TRUTH_TABLE = "map:tuple"
    JSON_MAP = "map:JSON"

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._client = redis.from_url(redis_url, decode_responses=True)

    def set_truth(self, key: uuid.UUID, status: str, version: int) -> None:
        value = json.dumps({"status": status, "version": version})
        self._client.hset(self.TRUTH_TABLE, str(key), value)

    def get_truth(self, key: uuid.UUID) -> Optional[dict]:
        data = self._client.hget(self.TRUTH_TABLE, str(key))
        return json.loads(data) if data else None

    def add_to_queue(self, capsule_id: uuid.UUID, del_time_epoch: float) -> None:
        self._client.zadd(self.QUEUE_KEY, {str(capsule_id): del_time_epoch})

    def del_queue(self, capsule_id: str) -> int:
        self._client.zrem(self.QUEUE_KEY, str(capsule_id))

    def add_to_JSONMap(self, capsule_id: uuid.UUID, json_payload: str) -> None:
        self._client.hset(self.JSON_MAP, str(capsule_id), json_payload)

    def del_from_JSONMap(self, capsule_id: uuid.UUID):
        self._client.hdel(str(capsule_id))


# factory
@lru_cache(maxsize=1)
def redis_connection() -> Redis_service:
    return Redis_service()
