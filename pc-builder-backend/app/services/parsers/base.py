from abc import ABC, abstractmethod

from app.models.entities import Store
from app.schemas.products import OfferImportItem


class StoreParser(ABC):
    @abstractmethod
    async def fetch(self, store: Store) -> list[OfferImportItem]:
        raise NotImplementedError
