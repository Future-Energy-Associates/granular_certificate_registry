import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown import markdown
from starlette.middleware.sessions import SessionMiddleware

from .crud import (
    account,
    certificate,
    device,
    organisations,
    storage,
    user,
)

load_dotenv()

STATIC_DIR_FP = os.path.abspath(
    os.getenv("STATIC_DIR_FP", "/code/gc_registry/api/static")
)
MIDDLEWARE_SECRET_KEY = os.environ["MIDDLEWARE_SECRET_KEY"]

descriptions = {}
for desc in ["api", "certificate", "storage"]:
    with open(Path(STATIC_DIR_FP, "descriptions", f"{desc}.md"), "r") as file:
        descriptions[desc] = markdown(file.read())

tags_metadata = [
    {
        "name": "Certificates",
        "description": descriptions["certificate"],
    },
    {
        "name": "Storage",
        "description": descriptions["storage"],
    },
    {
        "name": "Organisations",
        "description": "Top-level entities that manage multiple Users and Accounts.",
    },
    {
        "name": "Users",
        "description": "Individuals affiliated with an Organisation that can manage zero or more Accounts.",
    },
    {
        "name": "Accounts",
        "description": """Accounts receive GC Bundles issued from zero or more Devices, and can transfer them to other Accounts.
                        Can be managed by one or more Users with sufficient access privileges.""",
    },
    {
        "name": "Devices",
        "description": "Production or consumption units against which GC Bundles can be either issued or cancelled.",
    },
]

app = FastAPI(
    openapi_tags=tags_metadata,
    title="Energy Tag API Specification",
    description=descriptions["api"],
    version="2.0",
    contact={
        "name": "Please direct feedback to",
        "email": "connor@futureenergy.associates",
    },
    docs_url=None,
)

app.add_middleware(SessionMiddleware, secret_key=MIDDLEWARE_SECRET_KEY)

# app.include_router(authentication.router)
app.include_router(certificate.router, prefix="/certificates")
app.include_router(storage.router, prefix="/storage")
app.include_router(organisations.router, prefix="/organisations")
app.include_router(user.router, prefix="/users")
app.include_router(account.router, prefix="/accounts")
app.include_router(device.router, prefix="/devices")

openapi_data = app.openapi()

templates = Jinja2Templates(directory=f"{STATIC_DIR_FP}/templates")


@app.get("/", response_class=HTMLResponse, tags=["Core"])
async def read_root(request: Request):
    params = {
        "request": request,
        "head": {"title": "EnergyTag API Specification"},
        "body": [
            {"tag": "h1", "value": "EnergyTag API Specification"},
            {
                "tag": "p",
                "value": """This documentation outlines the first iteration of the EnergyTag
                            Granular Certificiate API Specification. Please direct all comments
                            to connor@futureenergy.associates""",
            },
            {
                "tag": "a",
                "tag_kwargs": {"href": f"{request.url._url}docs"},
                "value": "/docs",
            },
        ],
    }

    return templates.TemplateResponse("index.jinja", params)
