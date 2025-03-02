import datetime

from sqlalchemy import Engine
from sqlmodel import select, Session

from models import Shift, ShiftORM, Rotation
from store.shift import ShiftStore


class SQLAlchemyShiftStore(ShiftStore):
    def __init__(self, rotation: Rotation, engine: Engine) -> None:
        super().__init__(rotation)
        self._engine = engine

    def find(self, dt: datetime.datetime) -> Shift | None:
        stmt = (
            select(ShiftORM)
            .where(ShiftORM.start_date <= dt)
            .where(dt < ShiftORM.end_date)
        )
        with Session(self._engine) as session:
            result = session.exec(stmt).first()
            if result:
                return Shift.model_validate(result)
            return None

    def list(
        self, dt_from: datetime.datetime | None = None, limit: int | None = None
    ) -> list[Shift]:
        stmt = select(ShiftORM)
        if dt_from:
            stmt = stmt.where(ShiftORM.start_date > dt_from)
        if limit:
            stmt = stmt.limit(limit)

        with Session(self._engine) as session:
            result = session.exec(stmt).all()
            return [Shift.model_validate(row) for row in result]

    def create(self, shift: Shift) -> None:
        shift_orm = ShiftORM.model_validate(
            shift.model_dump() | {"rotation_id": self.rotation.id}
        )
        with Session(self._engine) as session:
            session.add(shift_orm)
            session.commit()

    def update(self, shift: Shift, new_shift: Shift) -> None:
        pass
