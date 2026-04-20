# models/mongo/base.py

from abc import ABC
from typing import ClassVar, List, Tuple


class MongoModel(ABC):
    __collection__: ClassVar[str]
    __indexes__: ClassVar[List[List[Tuple[str, int]]]] = []

    @classmethod
    def collection_name(cls) -> str:
        return cls.__collection__

    @classmethod
    def get_indexes(cls):
        return cls.__indexes__