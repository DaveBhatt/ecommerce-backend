from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas import UserCreate
from app.exceptions.auth import EmailAlreadyExistsError, UsernameAlreadyExistsError, InvalidCredentialsError

class AuthService:
    
    def register_user(self, db: Session, user_data: UserCreate,) -> User:
        
        existing_email = user_repository.get_by_email(db, user_data.email,)

        if existing_email:
            raise EmailAlreadyExistsError()
        
        existing_username = user_repository.get_by_username(db, user_data.username,)

        if existing_username:
            raise UsernameAlreadyExistsError()
        
        hashed_password = hash_password(user_data.password)

        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
        )

        return user_repository.create(db, user)


auth_service = AuthService()