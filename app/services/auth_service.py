from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository, user_repository
from app.schemas import UserCreate
from app.exceptions.auth import EmailAlreadyExistsError, UsernameAlreadyExistsError, InvalidCredentialsError
from app.core.security import verify_password, verify_access_token, create_access_token

class AuthService:

    def __init__(self, user_repository: UserRepository,):
        self.user_repository = user_repository
    
    def register_user(self, db: Session, user_data: UserCreate,) -> User:
        
        existing_email = self.user_repository.get_by_email(db, user_data.email,)

        if existing_email:
            raise EmailAlreadyExistsError()
        
        existing_username = self.user_repository.get_by_username(db, user_data.username,)

        if existing_username:
            raise UsernameAlreadyExistsError()
        
        hashed_password = hash_password(user_data.password)

        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
        )

        return self.user_repository.create(db, user)




    def authenticate_user(self, db: Session, email: str, password: str,) -> str:
        
        """This method:
        looks up the user
        verifies the password
        creates a JWT
        returns the token"""

        user = self.user_repository.get_by_email(db, email,)

        if user is None:
            raise InvalidCredentialsError()
        
        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise InvalidCredentialsError
        
        return create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
            }
        )





auth_service = AuthService(user_repository)