from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_lenght=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    full_name: str | None
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True) # This allows the model to be created from an ORM object, such as a SQLAlchemy model.


