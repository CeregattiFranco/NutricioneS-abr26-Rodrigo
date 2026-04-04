import redis
import os

url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
print(f"Testando conexão com {url}...")
try:
    r = redis.Redis.from_url(url, decode_responses=True)
    r.ping()
    print("PING OK!")
    keys = r.keys("*")
    print(f"Chaves encontradas: {keys}")
    token = r.get("nss:google:token")
    if token:
        print(f"Token encontrado! Tamanho: {len(token)}")
    else:
        print("Token nss:google:token NÃO encontrado.")
except Exception as e:
    print(f"ERRO: {e}")
