import logging
from abc import ABC, abstractmethod


class AbstractS3(ABC):
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    @abstractmethod
    def upload(self, image: bytes, remote_path: str, collection: str) -> None:
        pass

    @abstractmethod
    def download_to_file(self, remote_path_with_bucket: str, local_path: str) -> None:
        pass
