import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select
from starlette.requests import Request

from gc_registry import utils
from gc_registry.authentication.models import (
    APIUser,
    SecureAPIUser,
    Token,
    TokenBlacklist,
)
from gc_registry.core.database import db
from gc_registry.settings import settings

# router initialisation

router = APIRouter(tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_users_db = {
    "ayrton": {
        "username": "ayrton",
        "name": "Ayrton",
        "email": "ayrtonbourn@outlook.com",
        "picture": None,
        "hashed_password": "$2b$12$0NepEh/6tXYuc3uCYEuI3.BedxGqWecPrUoFV8SKOYvZ9NWTBCHeK",
        "scopes": None,
    }
}


CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# Auth functions


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_api_user(db, username: str) -> SecureAPIUser | None:
    if username in db:
        user_dict = db[username]
        return SecureAPIUser(**user_dict)
    else:
        return None


def authenticate_api_user(fake_db, username: str, password: str):
    user = get_api_user(fake_db, username)

    if not user:
        return False

    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.datetime.now(tz=datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
            minutes=15
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def is_token_blacklisted(oauth_token):
    with next(db.db_name_to_client["db_read"].yield_session()) as session:
        statement = select(TokenBlacklist).where(TokenBlacklist.token == oauth_token)
        results = session.exec(statement).all()

        if len(results) > 0:
            raise CredentialsException

    return


def validate_user_and_get_headers(oauth_token: str = Depends(oauth2_scheme)):
    headers = {}
    is_token_blacklisted(oauth_token)

    try:
        # extracting params in the JWT
        payload = jwt.decode(
            oauth_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub", "default")
        expire: str = payload.get("exp", "60")

        # checking the expiry date
        current_ts = datetime.datetime.now(tz=datetime.timezone.utc).timestamp()

        if (float(expire) - current_ts) < 0:
            with next(db.db_name_to_client["db_read"].yield_session()) as session:
                session.add(TokenBlacklist(token=oauth_token))
                session.commit()

        # checking username exists
        if username is None:
            raise CredentialsException

        get_api_user(fake_users_db, username=username)

    except JWTError:
        raise CredentialsException

    # providing refresh token if near expiry
    if (float(expire) - current_ts) < (settings.REFRESH_WARNING_MINS * 60):
        headers["refresh"] = "true"
    else:
        headers["refresh"] = "false"

    return headers


# Routes


@router.get("/user", response_model=APIUser)
def read_api_user(
    headers: dict = Depends(validate_user_and_get_headers),
    oauth_token: str = Depends(oauth2_scheme),
):
    payload = jwt.decode(
        oauth_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    username: str = payload.get("sub", "default")

    api_user = get_api_user(fake_users_db, username=username)

    return utils.format_json_response(api_user, headers, response_model=APIUser)


@router.get("/refresh", response_model=Token)
def refresh(oauth_token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(
        oauth_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    username: str = payload.get("sub", "default")

    oauth_token = create_access_token(
        data={"sub": username},
        expires_delta=datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": oauth_token, "token_type": "bearer"}


@router.get("/logout", response_model=Token)
def logout(
    request: Request,
    oauth_token: str = Depends(oauth2_scheme),
    session: Session = Depends(db.get_write_session),
):
    is_token_blacklisted(oauth_token)

    session.add(TokenBlacklist(token=oauth_token))
    session.commit()

    if "user" in request.session.keys():
        request.session.pop("user", None)

    return {"access_token": oauth_token, "token_type": "revoked"}


@router.post("/token", response_model=Token)
def token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_api_user(fake_users_db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = datetime.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token-params", response_model=Token)
def token_params(
    username: str | None = None,
    password: str | None = None,
):
    if username is not None and password is not None:
        user = authenticate_api_user(fake_users_db, username, password)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must specify a username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = datetime.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
