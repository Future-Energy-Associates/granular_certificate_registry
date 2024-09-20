from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown import markdown
from starlette.middleware.sessions import SessionMiddleware

from .account.routes import router as account_router
from .certificate.routes import router as certificate_router
from .device.routes import router as device_router
from .measurement.routes import router as measurements_router
from .organisation.routes import router as organisation_router
from .settings import settings
from .storage.routes import router as storage_router
from .user.routes import router as user_router

descriptions = {}
for desc in ["api", "certificate", "storage"]:
    with open(Path(settings.STATIC_DIR_FP, "descriptions", f"{desc}.md"), "r") as file:
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

app.add_middleware(SessionMiddleware, secret_key=settings.MIDDLEWARE_SECRET_KEY)

# app.include_router(authentication.router)
app.include_router(certificate_router, prefix="/certificates")
app.include_router(storage_router, prefix="/storage")
app.include_router(organisation_router, prefix="/organisations")
app.include_router(user_router, prefix="/users")
app.include_router(account_router, prefix="/accounts")
app.include_router(device_router, prefix="/devices")
app.include_router(measurements_router, prefix="/measurements")

openapi_data = app.openapi()

templates = Jinja2Templates(directory=f"{settings.STATIC_DIR_FP}/templates")


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
