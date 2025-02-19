import functools
from abc import abstractmethod
from typing import assert_never

from config import Config, Impl
from models import Rotation
from store.rotation import RotationStore, InMemoryRotationStore
from store.shift import ShiftStore, InMemoryShiftStore


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
