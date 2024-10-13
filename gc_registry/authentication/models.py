from sqlmodel import Field, SQLModel

from gc_registry.authentication.schemas import TokenBlacklistBase


class TokenBlacklist(TokenBlacklistBase, table=True):
    token: str = Field(primary_key=True)
    is_deleted: bool = Field(default=False)


class TokenBlacklistWrite(TokenBlacklistBase):
    token: str


class Token(SQLModel):
    access_token: str
    token_type: str


class APIUser(SQLModel):
    username: str = Field(primary_key=True)
    name: str
    email: str | None = None
    picture: str | None = None
    scopes: str | None = None


class SecureAPIUser(APIUser, table=True):
    hashed_password: str | None = None
    is_deleted: bool = Field(default=False)


class SecureAPIUserUpdate(SQLModel):
    username: str | None = None
    name: str | None = None
    email: str | None = None
    picture: str | None = None
    scopes: str | None = None
    hashed_password: str | None = None
