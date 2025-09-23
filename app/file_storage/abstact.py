import abc
from typing import IO

class AbstractFileStorage(abc.ABC):
    @abc.abstractmethod
    def save(self, file: IO, filename: str, content_type: str) -> str:
        raise NotImplementedError
    
    @abc.abstractmethod
    def delete(self, file_url: str) -> None:
        raise NotImplementedError