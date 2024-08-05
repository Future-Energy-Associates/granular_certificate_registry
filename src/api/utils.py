import json
from typing import List, Optional, Union

import sqlmodel
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlmodel import col


def parse_nans_to_null(json_str: str, replace_nan: bool = True):
    if replace_nan:
        json_str = json_str.replace("nan", "null")
        json_str = json_str.replace("NaN", "null")
        json_str = json_str.replace("None", "null")
    else:
        pass

    return json_str


def sqlmodel_obj_to_json(sqlmodel_obj, response_model=None, replace_nan=True):
    if sqlmodel_obj is None:
        return None
    elif isinstance(sqlmodel_obj, list):
        json_content = [
            json.loads(parse_nans_to_null(elem.json(), replace_nan))
            if response_model is None
            else json.loads(
                parse_nans_to_null(response_model.from_orm(elem).json(), replace_nan)
            )
            for elem in sqlmodel_obj
        ]
    elif response_model is not None:
        json_content = json.loads(
            parse_nans_to_null(
                response_model.from_orm(sqlmodel_obj).json(), replace_nan
            )
        )
    else:
        json_content = json.loads(parse_nans_to_null(sqlmodel_obj.json(), replace_nan))

    return json_content


def format_json_response(
    sqlmodel_obj,
    headers: dict = None,
    response_model=None,
    send_raw=False,
    pagination_metadata=None,
):
    if headers is None:
        headers = {}
    if send_raw:
        if pagination_metadata is not None:
            json_content = {
                "content": sqlmodel_obj,
                "pagination_metadata": pagination_metadata,
            }
        else:
            json_content = sqlmodel_obj

        return JSONResponse(content=json_content, headers=headers)

    if sqlmodel_obj is None:
        raise HTTPException(status_code=404, detail="Item not found")

    json_content = sqlmodel_obj_to_json(sqlmodel_obj, response_model=response_model)

    if pagination_metadata is not None:
        json_content = {
            "content": json_content,
            "pagination_metadata": pagination_metadata,
        }

    return JSONResponse(content=json_content, headers=headers)


def construct_pagination_metadata(
    locals_dict: dict,
    table_schema: sqlmodel.main.SQLModelMetaclass,
    session: sqlmodel.orm.session.Session,
    params: List[Optional[str]] = None,
    offset: int = 0,
    limit: int = 100,
    null_values: List[Union[str, None]] = None,
):
    if null_values is None:
        null_values = ["", None]
    if params is None:
        params = []
    query = session.query(table_schema)

    for param in params:
        value = locals_dict[param]

        if value not in null_values:
            query = query.filter(
                func.lower(col(getattr(table_schema, param))).contains(
                    value.strip().lower()
                )
            )

    pagination_metadata = {"count": query.count(), "offset": offset, "limit": limit}

    return pagination_metadata
