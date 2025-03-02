import functools
from abc import abstractmethod
from typing import assert_never

from sqlalchemy import Engine

from config import Config, Impl
from models import Rotation
from store.rotation import RotationStore
from store.rotation_mem import InMemoryRotationStore
from store.rotation_sql import SQLAlchemyRotationStore
from store.sa import global_engine
from store.shift import ShiftStore
from store.shift_mem import InMemoryShiftStore
from store.shift_sql import SQLAlchemyShiftStore


class StoreFactory:
    @abstractmethod
    def rotation(self) -> RotationStore: ...

    @abstractmethod
    def shifts(self, rotation: Rotation) -> ShiftStore: ...

    @classmethod
    def apply(cls, config: Config) -> "StoreFactory":
        match config.impl:
            case Impl.mem:
                return InMemoryStoreFactory()
            case Impl.sql:
                return SQLStoreFactory(global_engine())
            case default:
                assert_never(default)


class InMemoryStoreFactory(StoreFactory):
    """Cache instances in order to share in-memory rotations/shifts attached to cached instances."""

    @functools.cache
    def rotation(self) -> RotationStore:
        return InMemoryRotationStore()

    @functools.cache
    def shifts(self, rotation: Rotation) -> ShiftStore:
        return InMemoryShiftStore(rotation)


class SQLStoreFactory(StoreFactory):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def rotation(self) -> RotationStore:
        return SQLAlchemyRotationStore(self.engine)

    def shifts(self, rotation: Rotation) -> ShiftStore:
        return SQLAlchemyShiftStore(rotation, self.engine)
