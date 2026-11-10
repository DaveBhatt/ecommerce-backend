from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_db
from app.schemas import UserCreate, UserResponse, UserLogin, Token
from app.services.auth_service import auth_service
from app.exceptions.auth import EmailAlreadyExistsError, UsernameAlreadyExistsError, InvalidCredentialsError

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,)
async def register(user: UserCreate, db: AsyncSession = Depends(get_async_db)):

    try:
        return await auth_service.register_user(db, user,)
    
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, 
            detail="Email already registered",
        )
    
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

@router.post("/login", response_model=Token,)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_async_db),):

    try:
        token = await auth_service.authenticate_user(
            db,
            credentials.email,
            credentials.password,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }
    
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
