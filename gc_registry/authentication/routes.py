from datetime import datetime, timedelta

from esdbclient import EventStoreDBClient
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from gc_registry.authentication import services
from gc_registry.authentication.models import TokenRecords
from gc_registry.authentication.schemas import LoginRequest, Token
from gc_registry.core.database import db, events
from gc_registry.settings import settings as st

# router initialisation

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
    json_data: LoginRequest | None = None,
    write_session: Session = Depends(db.get_write_session),
    read_session: Session = Depends(db.get_read_session),
    esdb_client: EventStoreDBClient = Depends(events.get_esdb_client),
):
    """Login for access token.

    Accepts both OAuth2PasswordRequestForm and JSON request formats.

    OAuth2PasswordRequestForm requires the syntax "username" even though in practice
    we are using the user's email address.

    Args:
        form_data (OAuth2PasswordRequestForm, optional): The form data from the login request.
        json_data (LoginRequest, optional): The JSON data from the login request.
        write_session (Session): The database session to write to.
        read_session (Session): The database session to read from.
        esdb_client (EventStoreDBClient): The EventStoreDB client.

    Returns:
        Token: The access token.

    Raises:
        HTTPException: If invalid credentials are provided.
    """
    # Try to get credentials from JSON first, fall back to form data
    try:
        if json_data is not None:
            username = json_data.username
            password = json_data.password
        else:
            username = form_data.username
            password = form_data.password
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Invalid request format. Provide either valid JSON or form data.",
        )

    user = services.authenticate_user(username, password, read_session)

    if user.id is None:
        raise HTTPException(status_code=404, detail="User not found")

    access_token_expires = timedelta(minutes=st.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = services.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    token_record = TokenRecords(
        email=user.email,
        token=access_token,
        expires=datetime.now() + access_token_expires,
    )
    TokenRecords.create(token_record, write_session, read_session, esdb_client)

    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}
