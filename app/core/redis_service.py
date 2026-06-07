import redis.asyncio as redis

from app.auth.sсhemas import SessionCacheData

host = "redis",

redis_client = redis.Redis(
            host="redis",
            port=6379,
            decode_responses=True
        )


class SessionCache:

    PREFIX = "session"

    @classmethod
    async def set(cls, session_id: str, data: SessionCacheData, ttl: int):

        key = f"{cls.PREFIX}:{session_id}"

        await redis_client.set(
            name=key,
            value=data.model_dump_json(),
            ex=ttl
        )

    @classmethod
    async def get(cls, session_id: str) -> bool:
        value = await redis_client.get(f"{cls.PREFIX}:{session_id}")
        return value

    @classmethod
    async def delete(cls, session_id: str):
        await redis_client.delete(f"{cls.PREFIX}:{session_id}")

    @staticmethod
    async def refresh(session_id: str, ttl: int):
        await redis_client.expire(f"session:{session_id}", ttl)
