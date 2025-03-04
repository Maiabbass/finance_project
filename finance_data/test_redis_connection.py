import redis

# اتصال بـ Redis
r = redis.Redis(host='127.0.0.1', port=6379, db=0)

# اختبار الاتصال
try:
    response = r.ping()
    print("Redis is connected:", response)
except redis.ConnectionError as e:
    print("Error connecting to Redis:", e)
import redis

# اتصال بـ Redis
r = redis.Redis(host='127.0.0.1', port=6379, db=0)

# اختبار الاتصال
try:
    response = r.ping()
    print("Redis is connected:", response)
except redis.ConnectionError as e:
    print("Error connecting to Redis:", e)
