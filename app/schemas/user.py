from pydantic import BaseModel, EmailStr, ConfigDict, Field
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=100)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "john@example.com",
                    "username": "johndoe",
                    "password": "SecurePassword123!",
                    "full_name": "John Doe",
                }
            ]
        }
    )

class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "john@example.com",
                    "password": "SecurePassword123!",
                }
            ]
        }
    )

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: str | None
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True) # This allows the model to be created from an ORM object, such as a SQLAlchemy model.

class Token(BaseModel):
    access_token: str
    token_type: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "<jwt-access-token>",
                    "token_type": "bearer",
                }
            ]
        }
    )

