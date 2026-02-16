from typing import Optional
from pydantic import Field, BaseModel, EmailStr


class RequestRegister(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: str = EmailStr
    password: str = Field(min_length=6)
    first_name: Optional[str] = None
    last_name: Optional[str] = None