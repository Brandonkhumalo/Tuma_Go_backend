import dramatiq
from dramatiq.brokers.redis import RedisBroker
from decouple import config

redis_broker = RedisBroker(url=config("REDIS_URL"))
dramatiq.set_broker(redis_broker)