import datetime
import logging
from abc import abstractmethod, ABC

from models import Rotation

logger = logging.getLogger(__name__)


class RotationStore(ABC):
    @abstractmethod
    def get_by_id(self, id: str) -> Rotation | None: ...

    @abstractmethod
    def get_by_date(self, dt: datetime.datetime) -> Rotation | None: ...

    @abstractmethod
    def create(self, rotation: Rotation) -> None: ...


class InMemoryRotationStore(RotationStore):
    def __init__(self):
        self._rotations: dict[str, Rotation] = {}

    def create(self, rotation: Rotation) -> None:
        self._rotations[rotation.id] = rotation

    def get_by_id(self, id: str) -> Rotation | None:
        return self._rotations.get(id)

    def get_by_date(self, dt: datetime.datetime) -> Rotation | None:
        # explicit assignment is required for mypy: https://github.com/python/mypy/issues/14664
        rotation = min(
            [r for r in self._rotations.values() if r.start_date <= dt < r.end_date],
            key=lambda r: dt - r.start_date,
            default=None,
        )
        return rotation
