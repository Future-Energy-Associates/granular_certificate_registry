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
    email: str | None = None
    picture: str | None = None
    scopes: str | None = None


class SecureAPIUser(APIUser, table=True):
    hashed_password: str | None = None
