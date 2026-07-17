from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from jose import JWTError, jwt  # type: ignore
from app.core.config import settings

password_hasher = PasswordHash((BcryptHasher(),))

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(
        plain_password: str,
        hashed_password: str,
) -> bool:
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )

def create_access_token(data: dict,) -> str:

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def verify_access_token(token: str, ) -> dict:
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        return payload
    
    except JWTError:
        raise ValueError("Invalid Token")