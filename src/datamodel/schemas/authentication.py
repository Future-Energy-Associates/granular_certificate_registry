from sqlmodel import Field, SQLModel
from typing import Optional


class TokenBlacklistBase(SQLModel):
    pass


class TokenBlacklist(TokenBlacklistBase, table=True):
    token: str = Field(primary_key=True)


class TokenBlacklistWrite(TokenBlacklistBase):
    token: str


class Token(SQLModel):
    access_token: str
    token_type: str


class APIUser(SQLModel):
    username: str
    name: str
    email: Optional[str] = None
    picture: Optional[str] = None
    scopes: Optional[str] = None


class SecureAPIUser(APIUser):
    hashed_password: Optional[str] = None
