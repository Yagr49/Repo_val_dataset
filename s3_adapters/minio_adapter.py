import io
import json
import logging
import os

from s3_adapters.abstract.abstract_s3 import AbstractS3
from minio import Minio


class MinioAdapter(AbstractS3):
    """Adapter class for interacting with MinIO storage."""

    def __init__(self,
                 host: str = os.environ["MINIO_HOST"],
                 port: int = os.environ["MINIO_PORT"],
                 username: str = os.environ["MINIO_ROOT_USER"],
                 password: str = os.environ["MINIO_ROOT_PASSWORD"],
                 logger: logging.Logger = logging.getLogger(__name__)
                 ):
        """
         Initializes the MinioAdapter.

         Args:
             host (str): Host address of the MinIO server.
             port (int): Port number of the MinIO server.
             username (str): MinIO root username.
             password (str): MinIO root password.
             logger (logging.Logger): Logger instance for logging messages.
         """
        super().__init__(logger)
        self.client = Minio(f"{host}:{port}",
                            access_key=username,
                            secret_key=password,
                            secure=False)

    def upload(self, image: bytes, remote_path: str, collection: str) -> None:
        """
        Uploads a file from the local filesystem to a MinIO bucket.

        Args:
            image (bytes): The binary representation of the image to be uploaded.
            remote_path (str): Path where the file will be stored in the MinIO bucket.
            collection (str): Name of the MinIO bucket where the file will be uploaded.

        Raises:
            Exception: If the specified bucket does not exist and creation fails.
        """
        if not self.client.bucket_exists(collection):
            logging.warning(f'The BUCKET {collection} does not exist MINIO. ')
            self.logger.info(f'Creating new bucket {collection}.')
            self.client.make_bucket(collection)
            with open('./s3_adapters//bucket_policy.json', encoding='utf-8-sig') as f:
                bucket_policy = json.load(f)
                bucket_policy["Statement"][0]["Resource"] = [f"arn:aws:s3:::{collection}"]
                bucket_policy["Statement"][1]["Resource"] = [f"arn:aws:s3:::{collection}/*"]
            self.client.set_bucket_policy(collection, json.dumps(bucket_policy))

        self.client.put_object(collection, remote_path, io.BytesIO(image), len(image))
        self.logger.info(f"Image successfully uploaded as object {remote_path} to bucket {collection} - MINIO")

    def download_to_file(self, remote_path_with_bucket: str, local_path: str) -> None:
        """
        Downloads a file from a MinIO bucket to the local filesystem.

        Args:
            remote_path_with_bucket (str): Full path of the file in the format "bucket/remote_path".
            local_path (str): Local path where the file will be saved.

        Raises:
            ValueError: If the format of `remote_path_with_bucket` is incorrect.
        """
        try:
            bucket_name, object_name = remote_path_with_bucket.split("/", 1)
        except ValueError:
            raise ValueError("Invalid format for remote_path_with_bucket. Expected format: 'bucket/remote_path'.")

        self.client.fget_object(bucket_name, object_name, local_path)
        self.logger.info(f"{remote_path_with_bucket} successfully downloaded as file {local_path} - MINIO")
