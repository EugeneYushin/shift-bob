import datetime

from sqlalchemy import Engine
from sqlmodel import Session, select

from models import Rotation, RotationORM
from store.rotation import RotationStore
from sqlalchemy import func


class SQLAlchemyRotationStore(RotationStore):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_id(self, id: str) -> Rotation | None:
        stmt = select(RotationORM).where(RotationORM.id == id)
        with Session(self._engine) as session:
            result = session.exec(stmt).first()
            if result:
                return Rotation.model_validate(result)
            return None

    def get_by_date(self, dt: datetime.datetime) -> Rotation | None:
        stmt = (
            select(RotationORM)
            .where(RotationORM.start_date <= dt)
            .where(dt < RotationORM.end_date)
            .order_by(func.abs(dt - RotationORM.start_date))
        )
        with Session(self._engine) as session:
            result = session.exec(stmt).first()
            if result:
                return Rotation.model_validate(result)
            return None

    def create(self, rotation: Rotation) -> None:
        rotation_orm = RotationORM.model_validate(rotation.model_dump())
        with Session(self._engine) as session:
            session.add(rotation_orm)
            session.commit()
