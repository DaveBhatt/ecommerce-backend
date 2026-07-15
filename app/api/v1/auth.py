from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas import UserCreate, UserResponse
from app.services.auth_service import auth_service
from app.exceptions.auth import EmailAlreadyExistsError, UsernameAlreadyExistsError, InvalidCredentialsError

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,)

def register(user: UserCreate, db: Session = Depends(get_db)):

    try:
        return auth_service.register_user(db, user,)
    
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=409, 
            detail="Email already registered",
        )
    
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

