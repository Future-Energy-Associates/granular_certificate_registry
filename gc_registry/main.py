import datetime
import logging
from pathlib import Path
from typing import Callable

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown import markdown
from pyinstrument import Profiler
from pyinstrument.renderers.html import HTMLRenderer
from pyinstrument.renderers.speedscope import SpeedscopeRenderer
from starlette.middleware.sessions import SessionMiddleware

from .account.routes import router as account_router
from .certificate.routes import router as certificate_router
from .core.database.db import get_db_name_to_client
from .core.models.base import LoggingLevelRequest
from .device.routes import router as device_router
from .logging_config import logger, set_logger_and_children_level
from .measurement.routes import router as measurements_router
from .settings import settings
from .storage.routes import router as storage_router
from .user.routes import router as user_router

STATIC_DIR_FP = Path(__file__).parent / "static"

descriptions = {}
for desc in ["api", "certificate", "storage"]:
    static_dir = STATIC_DIR_FP / "descriptions" / f"{desc}.md"
    with open(static_dir, "r") as file:
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
    dependencies=[Depends(get_db_name_to_client)],
)

app.add_middleware(SessionMiddleware, secret_key=settings.MIDDLEWARE_SECRET_KEY)

# add instantiated instance of sync functionality here

# app.include_router(authentication.router)
app.include_router(
    certificate_router,
    prefix="/certificate",
)
app.include_router(
    storage_router,
    prefix="/storage",
)
app.include_router(
    user_router,
    prefix="/user",
)
app.include_router(
    account_router,
    prefix="/account",
)
app.include_router(
    device_router,
    prefix="/device",
)
app.include_router(
    measurements_router,
    prefix="/measurement",
)

openapi_data = app.openapi()

templates = Jinja2Templates(directory=STATIC_DIR_FP / "templates")


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
                "tag_kwargs": {"href": f"{request.url._url}redoc"},
                "value": "/redoc",
            },
        ],
    }

    return templates.TemplateResponse("index.jinja", params)


# Assemble fastapi loggers
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_access_logger = logging.getLogger("uvicorn.access")
fastapi_logger = logging.getLogger("fastapi")


@app.post("/change_log_level", tags=["Core"])
async def change_log_level_endpoint(request: LoggingLevelRequest):
    """Change the logging level at runtime for all relevant loggers."""
    global logger, uvicorn_logger, uvicorn_access_logger, fastapi_logger

    numeric_level = getattr(logging, request.level)

    # List of all loggers to modify
    loggers_to_update = [
        logger,  # Application logger
        uvicorn_logger,  # Main Uvicorn logger
        uvicorn_access_logger,  # Uvicorn access log
        fastapi_logger,  # FastAPI logger
    ]

    for logger_instance in loggers_to_update:
        set_logger_and_children_level(logger_instance, numeric_level)

    # Debug information to verify changes
    debug_info = {}
    for logger_instance in loggers_to_update:
        # Handle root logger specially
        current_name = logger_instance.name if logger_instance.name else "root"

        debug_info[current_name] = {
            "effective_level": logging.getLevelName(
                logger_instance.getEffectiveLevel()
            ),
            "handlers": [
                {"handler": str(handler), "level": logging.getLevelName(handler.level)}
                for handler in logger_instance.handlers
            ],
        }

        # Add information about child loggers
        if logger_instance.name:  # Skip for root logger
            children = [
                name
                for name in logging.root.manager.loggerDict
                if name.startswith(logger_instance.name + ".")
            ]
            for child_name in children:
                child_logger = logging.getLogger(child_name)
                debug_info[child_name] = {
                    "effective_level": logging.getLevelName(
                        child_logger.getEffectiveLevel()
                    ),
                    "handlers": [
                        {
                            "handler": str(handler),
                            "level": logging.getLevelName(handler.level),
                        }
                        for handler in child_logger.handlers
                    ],
                }

    return {
        "message": f"Log level changed to {request.level}",
        "logger_status": debug_info,
    }


if settings.PROFILING_ENABLED:
    profile_type: str = "html"

    @app.middleware("http")
    async def profile_request(request: Request, call_next: Callable):
        """Profile the current request

        Taken from https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi
        with small improvements.

        """
        # we map a profile type to a file extension, as well as a pyinstrument profile renderer
        profile_type_to_ext = {"html": "html", "speedscope": "speedscope.json"}
        profile_type_to_renderer = {
            "html": HTMLRenderer,
            "speedscope": SpeedscopeRenderer,
        }

        # we profile the request along with all additional middlewares, by interrupting
        # the program every 1ms1 and records the entire stack at that point
        with Profiler(interval=0.001, async_mode="enabled") as profiler:
            response = await call_next(request)

        # we dump the profiling into a file
        extension = profile_type_to_ext[profile_type]
        renderer = profile_type_to_renderer[profile_type]()

        # create a new dated folder in core/profiling with todays date
        todays_date = datetime.datetime.now().strftime("%Y-%m-%d")
        profiling_dir = Path(__file__).parent / "core" / "profiling" / todays_date
        profiling_dir.mkdir(exist_ok=True)

        with open(Path(profiling_dir, f"profile.{extension}"), "w") as out:
            out.write(profiler.output(renderer=renderer))
        return response
