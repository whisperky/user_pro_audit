from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:111@localhost:5432/user_profiles")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "111")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    print("Database URL:", DATABASE_URL)
    print("Secret Key:", SECRET_KEY)
    print("Algorithm:", ALGORITHM)
    print("Access Token Expiry (minutes):", ACCESS_TOKEN_EXPIRE_MINUTES)
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
