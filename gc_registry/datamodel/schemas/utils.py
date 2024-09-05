from typing import Union

from fastapi import HTTPException
from sqlmodel import SQLModel, select


class ActiveRecord(SQLModel):
    @classmethod
    def by_id(cls, id_: int, session):
        obj = session.get(cls, id_)
        if obj is None:
            raise HTTPException(
                status_code=404, detail=f"{cls.__name__} with id {id_} not found"
            )
        return obj

    @classmethod
    def all(cls, session):
        return session.exec(select(cls)).all()

    @classmethod
    def create(cls, source: Union[dict, SQLModel], session):
        if isinstance(source, SQLModel):
            obj = cls.from_orm(source)
        elif isinstance(source, dict):
            obj = cls.parse_obj(source)
        else:
            raise ValueError(f"The input type {type(source)} can not be processed")

        session.add(obj)
        session.commit()
        session.refresh(obj)

        return obj

    def save(self, session):
        session.add(self)
        session.commit()
        session.refresh(self)

    def update(self, source: Union[dict, SQLModel], session):
        if isinstance(source, SQLModel):
            source = source.dict(exclude_unset=True)

        for key, value in source.items():
            setattr(self, key, value)
        self.save(session)

    def delete(self, session):
        session.delete(self)
        session.commit()
