import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .api.routers import (
    accounts,
    certificates,
    devices,
    organisations,
    storage,
    users,
)

# App initialisation
load_dotenv()

static_dir_fp = os.getenv("STATIC_DIR_FP", "/code/src/api/static")
static_dir_fp = os.path.abspath(static_dir_fp)
middleware_secret_key = os.environ["MIDDLEWARE_SECRET_KEY"]

gc_description = """GC lifecycle management functionality. Filtering of GC Bundles for action implementation and queries
should be flexible for the end user and accommodate any combination of search parameters below for a specific Account:
<br>
- **Certificate Issuance ID** - Returns all GC Bundles with the specified Issuance ID. Implicitly limited to single Device and time period.\n
- **Bundle ID Range** - If Issuance ID is provided, returns a GC Bundle with certificate IDs inclusive of and between the integer GC Bundle ID range specified.\n
- **Issuance Time Period** - Returns all GC Bundles issued for generation that occured within the specified time period. If no Device is provided, result can include GC Bundles from multiple Devices.\n
- **Energy Source** - Returns all GC Bundles issued for generation derived from the specified energy source.\n
- **Production Device ID** - Returns all GC Bundles issued to the specified production Device.\n"""

storage_description = """The Storage Charge Record (SCR) is a record of the energy charged into a Storage Device from the grid or directly from another energy source.
All charging events must be recorded in an SCR following verification of metering reports from the storage unit.
Once recorded, an SCR can be allocated to a cancelled GC bundle issued in the same time period as the charging interval,
retaining the attributes of the GCs representing the energy charged. The Registry must ensure that a
process is in place to verify that the energy charged into the Storage Device is not double-counted or mismatched to the wrong
number of cancelled GC Bundles, and that the cancelled GC Bundles were issued within the charging interval indicated in the SCR.
<br>\n
A suggested approach to applying this requirement is to enforce a one-to-one relationship between SCRs and the cancelled GC Bundles,
allowing the full set of GC Bundle attributes to be referenced from the SCR and the subsequent SDR/SD-GC Bundle as a
single dependent chain without needing any aggregation or weighting algorithms. A disadvantage of this approach is that only a single
contiguous range of GC Bundle IDs can be allocated to each SCR, which in practice may lead to a large number of SCRs created due to
multiple non-contiguous GC Bundles being allocated in the same charging interval. More details can be found in the White Paper.
<br>\n
The Storage Discharge Record (SDR) is a record of the energy discharged by a Storage Device into the grid.
It is issued following the verification of a cancelled GC Bundle, a matching allocated SCR, and the proper allocation
of Storage Losses incurred during the charge interval. It is recommended that the methodology with which Storage Device
operators are permitted to allocate SDRs to SCRs, whether LIFO, FIFO, a weighted average, or operator's discretion, is
fixed such that operators cannot change the methodology in a way that would allow them to manipulate the allocation of SDRs.
<br>\n
To comply with the Standard, the Registry must provide a process to view the attributes of the underlying GC Bundles that
have been cancelled leading to the issuance of the SCR allocated to this SDR, by following the chain of one-to-one foreign
keys from the SDR to the SCR, and from the SCR to the cancelled GC Bundles.
<br>\n
The method for calulating the storage loss is not mandated, but the Registry must ensure that the method used is transparent and
clearly documented for auditing purposes. The method proposed in this API Specification followed the suggested methodology in the
EnergyTag Standard, which is to calculate the storage losses as the difference between the total input and output energy
of the Storage Device over a specified interval period (which shall not exceed 6 months for the initial efficiency factor
calculated from the start-up date of the Storage Device), implicitly including parasitic losses."""

tags_metadata = [
    {
        "name": "Certificates",
        "description": gc_description,
    },
    {
        "name": "Storage",
        "description": storage_description,
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
    # {
    #     "name": "Miscellaneous",
    #     "description": """Additional objects that represent consistent additional information about the entities above.
    #                       These objects do not form part of the EnergyTag API Standard and are included here for completeness.""",
    # },
]

api_description = """
This document outlines the EnergyTag API Specification to accompany Version 2 of
the EnergyTag Standard.
The functionality outlined within each API interaction represents the recommended
minimum required detail necessary to implement a consistent Granular Certificate
(GC) registry system.
Within the Certificates section, the definition of GCs as specified in the Create
Certificate POST request, alongside the filtering parameters required to instigate
query, transfer, and cancellation requests, will form core components of the standard
and impact the functionality of the registry the greatest. Subsequent sections
describing Organisation, User, Account, and Device management are **recommendations
only** and do not form part of the standard, although terminology used therein is
referenced in the certificate definitions. They are included in the database class
diagram for the sake of completeness in representing the relationships between the
certificate and action definitions; the fields implemented for these tables are
left to the discretion of the registry operator.
<br>\n
Where Universally Unique Identifiers (UUIDs) have been used, these can be replaced with
any consistent and unique identification mechanism preferred by the registry; for
example, concatenations of datetime and Device ID). It is recommended that GC Bundle
IDs remain represented as integers, or an initial string concatenated with an integer,
that can be both uniquely referenced and unambiguously incremented to simplify the
GC Bundle subdivision process.
<br>\n
Each API call defined below is to be interpreted as an instance of an object that is
stored by the registry upon receipt by a User, and can be updated as it moves from
received, through pending, to resolved within a transaction log uniquely identified
by an action ID. With this in mind, fields such as `action_completed_datetime` are
not to be interpreted as attributes supplied by the User, but fields that are
populated and updated by the registry as the request is processed.
This approach allows any and all actions to be queried and traced, with relevant
User access rights left to the discretion of the registry operator.
<br>\n
[Click here](https://pasteboard.co/KHFQcxYCoRPL.png) to view the GC model class diagram
for this specification, [here](https://pasteboard.co/KHFQcxYCoRPL.png) for the Storage class diagram and
[click here](https://pasteboard.co/KIRLh9VKr2KO.png) to
view a graphical example of a GC Bundle issuance, transfer, and cancellation that
illustrates the principles of the GC Bundle subdivision and management processes.

"""
app = FastAPI(
    openapi_tags=tags_metadata,
    title="Energy Tag API Specification",
    description=api_description,
    version="2.0",
    contact={
        "name": "Please direct feedback to",
        "email": "connor@futureenergy.associates",
    },
    docs_url=None,
)

app.add_middleware(SessionMiddleware, secret_key=middleware_secret_key)

# app.include_router(authentication.router)
app.include_router(certificates.router, prefix="/certificates")
app.include_router(storage.router, prefix="/storage")
app.include_router(organisations.router, prefix="/organisations")
app.include_router(users.router, prefix="/users")
app.include_router(accounts.router, prefix="/accounts")
app.include_router(devices.router, prefix="/devices")

# app.mount("/static", StaticFiles(directory=static_dir_fp), name="static")


# @app.on_event("startup")
# def save_openapi_json():
openapi_data = app.openapi()

templates = Jinja2Templates(directory=f"{static_dir_fp}/templates")


# Routes
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
