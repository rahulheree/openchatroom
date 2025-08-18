import secrets
from itsdangerous import URLSafeTimedSerializer
from app.settings import settings
from typing import Optional 

serializer = URLSafeTimedSerializer(settings.SESSION_SECRET_KEY)

def create_session_id() -> str:
    return secrets.token_hex(16)

def create_join_token(user_id: int) -> str:
    return serializer.dumps(user_id)

def verify_join_token(token: str) -> Optional[int]:
    try:
        user_id = serializer.loads(token, max_age=86400)
        return user_id
    except Exception:
        return None