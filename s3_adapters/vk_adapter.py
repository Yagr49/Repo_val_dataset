import logging
import os

import boto3

from botocore.config import Config
from s3_adapters.abstract.abstract_s3 import AbstractS3


class VkAdapter(AbstractS3):
    """Adapter class for interacting with S3 storage using the VKCloud service."""

    def __init__(
            self,
            access_key: str = os.environ["AWS_ACCESS_KEY_ID"],
            secret_key: str = os.environ["AWS_SECRET_ACCESS_KEY"],
            endpoint_url: str = os.environ["AWS_ENDPOINT_URL"],
            sse_custom_key: str = os.environ["SSE_CUSTOM_KEY"],
            sse_custom_algorithm: str = os.environ["SSE_CUSTOM_ALGORITHM"],
            logger: logging.Logger = logging.getLogger(__name__),
    ):
        """
        Initializes the VkAdapter.

        Args:
            access_key (str): AWS access key ID.
            secret_key (str): AWS secret access key.
            endpoint_url (str): Endpoint URL for the S3 service.
            logger (logging.Logger): Logger instance for logging messages.
        """
        super().__init__(logger)
        self.access_key = access_key
        self.secret_key = secret_key
        self.sse_custom_key = sse_custom_key
        self.sse_custom_algorithm = sse_custom_algorithm

        self.session = boto3.session.Session()

        self.client = self.session.client(service_name="s3",
                                          aws_access_key_id=access_key,
                                          aws_secret_access_key=secret_key,
                                          endpoint_url=endpoint_url,
                                          region_name='ru-msk',
                                          config=Config(
                                              request_checksum_calculation="when_required",
                                              response_checksum_validation="when_required"
                                          )
                                          )

    def upload(self, data: bytes, remote_path: str, collection: str) -> None:
        """
        Uploads a file from the local filesystem to an S3 bucket.

        Args:
            data (bytes): The binary representation of the data to be uploaded.
            remote_path (str): Path where the file will be stored in the S3 bucket.
            collection (str): Name of the S3 bucket where the file will be uploaded.

        Raises:
            Exception: If the specified bucket does not exist.
        """

        try:
            self.logger.info(self.client.list_buckets())
            existing_buckets = [
                buck["Name"] for buck in self.client.list_buckets()["Buckets"]
            ]
        except Exception:
            raise
        if collection not in existing_buckets:
            raise Exception(f"The BUCKET {collection} does not exist VKCLOUD")

        self.logger.info(remote_path)
        self.client.put_object(
            Bucket=collection,
            Key=remote_path,
            Body=data,
            SSECustomerKey=self.sse_custom_key,
            SSECustomerAlgorithm=self.sse_custom_algorithm,
        )

        self.logger.info(
            f"Image successfully uploaded as object {remote_path} to bucket {collection} - VKCLOUD"
        )

    def download_to_file(self, remote_path_with_bucket: str, local_path: str) -> None:
        """
        Downloads a file from an S3 bucket to the local filesystem.

        Args:
            remote_path_with_bucket (str): Full path of the file in the format "bucket/remote_path".
            local_path (str): Local path where the file will be saved.

        Raises:
            ValueError: If the format of `remote_path_with_bucket` is incorrect.
        """
        try:
            collection, remote_path = remote_path_with_bucket.split("/", 1)
        except ValueError:
            raise ValueError(
                "Invalid format for remote_path_with_bucket. Expected format: 'bucket/remote_path'."
            )
        self.client.download_file(
            Bucket=collection,
            Key=remote_path,
            Filename=local_path,
            ExtraArgs={
                'SSECustomerAlgorithm': self.sse_custom_algorithm,
                'SSECustomerKey': self.sse_custom_key
            }
        )
        self.logger.info(
            f"{remote_path_with_bucket} successfully downloaded as file {local_path} - VKCLOUD"
        )
