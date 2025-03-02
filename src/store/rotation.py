import datetime
import logging
from abc import ABC, abstractmethod

from models import Rotation

logger = logging.getLogger(__name__)


class RotationStore(ABC):
    @abstractmethod
    def get_by_id(self, id: str) -> Rotation | None: ...

    @abstractmethod
    # TODO unify naming with ShiftStore, ie get_by_date vs find
    def get_by_date(self, dt: datetime.datetime) -> Rotation | None: ...

    @abstractmethod
    def create(self, rotation: Rotation) -> None: ...
