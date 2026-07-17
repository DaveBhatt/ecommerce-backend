from uuid import UUID

from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import verify_access_token
from app.database.session import get_db
from app.repositories.user_repository import user_repository

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login",)
security = HTTPBearer()

def get_current_user(
    # token: str = Depends(oauth2_scheme), 
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    
    """This dependency performs three important checks:
        verifies the token,
        ensures the user still exists,
        ensures the account is active."""
    
    token = credentials.credentials
    
    try:
        payload = verify_access_token(token)
        user_id = UUID(payload["sub"])
    
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    user = user_repository.get_by_id(db, user_id,)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    return user



