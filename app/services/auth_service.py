from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository, user_repository
from app.schemas import UserCreate
from app.exceptions.auth import EmailAlreadyExistsError, UsernameAlreadyExistsError, InvalidCredentialsError

class AuthService:

    def __init__(self, user_repository: UserRepository,):
        self.user_repository = user_repository
    
    async def register_user(self, db: AsyncSession, user_data: UserCreate,) -> User:
        
        existing_email = await self.user_repository.get_by_email(db, user_data.email,)

        if existing_email:
            raise EmailAlreadyExistsError()
        
        existing_username = await self.user_repository.get_by_username(db, user_data.username,)

        if existing_username:
            raise UsernameAlreadyExistsError()
        
        hashed_password = hash_password(user_data.password)

        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
        )

        return await self.user_repository.create(db, user)


    async def authenticate_user(self, db: AsyncSession, email: str, password: str,) -> str:
        
        """This method:
        looks up the user
        verifies the password
        creates a JWT
        returns the token"""

        user = await self.user_repository.get_by_email(db, email,)

        if user is None:
            raise InvalidCredentialsError()
        
        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise InvalidCredentialsError()
        
        return create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
            }
        )


auth_service = AuthService(user_repository)