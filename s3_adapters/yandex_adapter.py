import logging
import os

import boto3
from botocore.config import Config

from s3_adapters.abstract.abstract_s3 import AbstractS3


class YandexAdapter(AbstractS3):
    """Adapter for Yandex Cloud Object Storage (S3-compatible, no SSE-C)."""

    def __init__(
        self,
        access_key: str = os.environ["AWS_ACCESS_KEY_ID"],
        secret_key: str = os.environ["AWS_SECRET_ACCESS_KEY"],
        endpoint_url: str = os.environ["AWS_ENDPOINT_URL"],
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        super().__init__(logger)
        session = boto3.session.Session()
        self.client = session.client(
            service_name="s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            region_name="ru-central1",
            config=Config(
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def upload(self, data: bytes, remote_path: str, collection: str) -> None:
        self.client.put_object(Bucket=collection, Key=remote_path, Body=data)
        self.logger.info(f"Uploaded {remote_path} to {collection} - Yandex S3")

    def download_to_file(self, remote_path_with_bucket: str, local_path: str) -> None:
        try:
            collection, remote_path = remote_path_with_bucket.split("/", 1)
        except ValueError:
            raise ValueError("Invalid format. Expected: 'bucket/remote_path'.")
        self.client.download_file(Bucket=collection, Key=remote_path, Filename=local_path)
        self.logger.info(f"Downloaded {remote_path_with_bucket} to {local_path} - Yandex S3")
