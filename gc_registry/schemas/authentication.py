from typing import Optional

from sqlmodel import Field, SQLModel

from gc_registry.models.authentication import TokenBlacklistBase


class TokenBlacklist(TokenBlacklistBase, table=True):
    token: str = Field(primary_key=True)


class TokenBlacklistWrite(TokenBlacklistBase):
    token: str


class Token(SQLModel):
    access_token: str
    token_type: str


class APIUser(SQLModel):
    username: str = Field(primary_key=True)
    name: str
    email: Optional[str] = None
    picture: Optional[str] = None
    scopes: Optional[str] = None


class SecureAPIUser(APIUser, table=True):
    hashed_password: Optional[str] = None
