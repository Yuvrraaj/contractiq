import re
from sqlmodel import SQLModel, Field
from pydantic import field_validator, model_validator


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: str


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = True


class UserCreate(UserBase):
    password: str

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        """Runs after type validation. v is already confirmed to be a str."""
        v = v.lower().strip()
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v  # always return the (possibly transformed) value

    @field_validator("full_name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return v.title()  # auto-capitalise: "yuvraj jha" → "Yuvraj Jha"

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserPublic(UserBase):
    id: int


class UserWithStats(UserPublic):
    """Extended response that includes computed info — used in profile endpoint."""
    contract_count: int = 0