"""
Project : Enterprise Banking Analytics Platform

File    : s3_uploader.py

Description
-----------
Uploads generated Parquet datasets to the
Amazon S3 raw data zone.

Features
--------
- Idempotent uploads
- Multipart transfer configuration
- Dataset partitioning
- Retry handling
- Structured logging
- Object metadata
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import argparse
from datetime import date
import boto3

from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
)

from generators.common.config import (
    AWS_REGION,
    RAW_DATA_DIR,
    S3_RAW_BUCKET,
    S3_RAW_PREFIX,
)

from generators.common.logger import get_logger


DATASETS = (
    "branches",
    "employees",
    "customers",
    "accounts",
    "loans",
    "credit_cards",
    "transactions",
    "fraud",
)


class S3RawUploader:
    """
    Upload Parquet datasets to S3 raw zone.
    """

    def __init__(self) -> None:

        self.logger = get_logger(
            self.__class__.__name__
        )

        self.raw_data_dir = Path(
            RAW_DATA_DIR
        )

        self.bucket = S3_RAW_BUCKET

        self.prefix = S3_RAW_PREFIX

        boto_config = Config(
            region_name=AWS_REGION,
            retries={
                "max_attempts": 5,
                "mode": "adaptive",
            },
        )

        self.s3_client = boto3.client(
            "s3",
            config=boto_config,
        )

        self.transfer_config = TransferConfig(
            multipart_threshold=64 * 1024 * 1024,
            multipart_chunksize=64 * 1024 * 1024,
            max_concurrency=10,
            use_threads=True,
        )

    # --------------------------------------------------------------

    @staticmethod
    def calculate_md5(
        file_path: Path,
    ) -> str:
        """
        Calculate local file MD5 checksum.
        """

        digest = hashlib.md5(
            usedforsecurity=False
        )

        with file_path.open("rb") as file_handle:

            for chunk in iter(
                lambda: file_handle.read(
                    1024 * 1024
                ),
                b"",
            ):
                digest.update(chunk)

        return digest.hexdigest()

    # --------------------------------------------------------------

    def object_key(
        self,
        dataset_name: str,
        file_path: Path,
    ) -> str:
        """
        Build deterministic S3 object key.
        """

        return (
            f"{self.prefix}/"
            f"{dataset_name}/"
            f"{file_path.name}"
        )

    # --------------------------------------------------------------

    def remote_checksum(
        self,
        object_key: str,
    ) -> str | None:
        """
        Read checksum from S3 object metadata.
        """

        try:

            response = self.s3_client.head_object(
                Bucket=self.bucket,
                Key=object_key,
            )

            return response.get(
                "Metadata",
                {},
            ).get(
                "source-md5"
            )

        except ClientError as error:

            error_code = (
                error.response
                .get("Error", {})
                .get("Code")
            )

            if error_code in {
                "404",
                "NoSuchKey",
                "NotFound",
            }:
                return None

            raise

    # --------------------------------------------------------------

    def should_upload(
        self,
        file_path: Path,
        object_key: str,
    ) -> tuple[bool, str]:
        """
        Determine whether object requires upload.
        """

        local_checksum = self.calculate_md5(
            file_path
        )

        remote_checksum = self.remote_checksum(
            object_key
        )

        return (
            local_checksum != remote_checksum,
            local_checksum,
        )

    # --------------------------------------------------------------

    def upload_file(
        self,
        dataset_name: str,
        file_path: Path,
    ) -> bool:
        """
        Upload one Parquet file.
        """

        object_key = self.object_key(
            dataset_name,
            file_path,
        )

        try:

            (
                requires_upload,
                checksum,
            ) = self.should_upload(
                file_path,
                object_key,
            )

            if not requires_upload:

                self.logger.info(
                    "Skipping unchanged object: s3://%s/%s",
                    self.bucket,
                    object_key,
                )

                return False

            self.logger.info(
                "Uploading: %s -> s3://%s/%s",
                file_path,
                self.bucket,
                object_key,
            )

            self.s3_client.upload_file(
                Filename=str(file_path),
                Bucket=self.bucket,
                Key=object_key,
                ExtraArgs={
                    "ContentType":
                        "application/octet-stream",
                    "Metadata": {
                        "dataset":
                            dataset_name,
                        "source-md5":
                            checksum,
                        "record-format":
                            "parquet",
                    },
                },
                Config=self.transfer_config,
            )

            return True

        except (
            ClientError,
            BotoCoreError,
        ):

            self.logger.exception(
                "Failed to upload file: %s",
                file_path,
            )

            raise

    # --------------------------------------------------------------

    def upload_dataset(
        self,
        dataset_name: str,
    ) -> tuple[int, int]:
        """
        Upload one complete dataset.
        """

        dataset_directory = (
            self.raw_data_dir
            / dataset_name
        )

        parquet_files = sorted(
            dataset_directory.glob(
                "*.parquet"
            )
        )

        if not parquet_files:

            self.logger.warning(
                "No Parquet files found: %s",
                dataset_name,
            )

            return 0, 0

        uploaded = 0

        skipped = 0

        for file_path in parquet_files:

            if self.upload_file(
                dataset_name,
                file_path,
            ):
                uploaded += 1

            else:
                skipped += 1

        return uploaded, skipped

    # --------------------------------------------------------------

    def run(self) -> None:
        """
        Upload all generated datasets.
        """

        self.logger.info(
            "Starting S3 raw-zone upload"
        )

        total_uploaded = 0

        total_skipped = 0

        for dataset_name in DATASETS:

            self.logger.info(
                "Processing dataset: %s",
                dataset_name,
            )

            uploaded, skipped = (
                self.upload_dataset(
                    dataset_name
                )
            )

            total_uploaded += uploaded

            total_skipped += skipped

            self.logger.info(
                "Dataset completed: %s | "
                "uploaded=%s | skipped=%s",
                dataset_name,
                uploaded,
                skipped,
            )

        self.logger.info(
            "S3 upload completed | "
            "uploaded=%s | skipped=%s",
            total_uploaded,
            total_skipped,
        )

class S3DailyPartitionUploader:
    """
    Upload Airflow execution-date partitions
    to the S3 raw zone.

    S3 layout
    ---------
    raw/transactions/
        transaction_date=YYYY-MM-DD/

    raw/fraud/
        detection_date=YYYY-MM-DD/
    """

    DATASETS = {
        "transactions": {
            "local_dataset": "transactions_daily",
            "partition_key": "transaction_date",
        },
        "fraud": {
            "local_dataset": "fraud_daily",
            "partition_key": "detection_date",
        },
    }

    def __init__(
        self,
        execution_date: date,
    ) -> None:

        self.execution_date = execution_date

        self.logger = get_logger(
            self.__class__.__name__
        )

        self.raw_data_dir = Path(
            RAW_DATA_DIR
        )

        self.bucket = S3_RAW_BUCKET

        self.prefix = S3_RAW_PREFIX

        boto_config = Config(
            region_name=AWS_REGION,
            retries={
                "max_attempts": 5,
                "mode": "adaptive",
            },
        )

        self.s3_client = boto3.client(
            "s3",
            config=boto_config,
        )

        self.transfer_config = TransferConfig(
            multipart_threshold=(
                64 * 1024 * 1024
            ),
            multipart_chunksize=(
                64 * 1024 * 1024
            ),
            max_concurrency=10,
            use_threads=True,
        )

    # --------------------------------------------------------------

    @staticmethod
    def calculate_md5(
        file_path: Path,
    ) -> str:
        """
        Calculate source-file MD5.
        """

        digest = hashlib.md5(
            usedforsecurity=False
        )

        with file_path.open("rb") as file_handle:

            for chunk in iter(
                lambda: file_handle.read(
                    1024 * 1024
                ),
                b"",
            ):
                digest.update(chunk)

        return digest.hexdigest()

    # --------------------------------------------------------------

    def partition_name(
        self,
        partition_key: str,
    ) -> str:

        return (
            f"{partition_key}="
            f"{self.execution_date.isoformat()}"
        )

    # --------------------------------------------------------------

    def local_partition(
        self,
        local_dataset: str,
        partition_key: str,
    ) -> Path:

        return (
            self.raw_data_dir
            / local_dataset
            / self.partition_name(
                partition_key
            )
        )

    # --------------------------------------------------------------

    def object_key(
        self,
        dataset_name: str,
        partition_key: str,
        file_path: Path,
    ) -> str:

        return (
            f"{self.prefix}/"
            f"{dataset_name}/"
            f"{self.partition_name(partition_key)}/"
            f"{file_path.name}"
        )

    # --------------------------------------------------------------

    def remote_checksum(
        self,
        object_key: str,
    ) -> str | None:

        try:

            response = self.s3_client.head_object(
                Bucket=self.bucket,
                Key=object_key,
            )

            return (
                response
                .get("Metadata", {})
                .get("source-md5")
            )

        except ClientError as error:

            error_code = (
                error.response
                .get("Error", {})
                .get("Code")
            )

            if error_code in {
                "404",
                "NoSuchKey",
                "NotFound",
            }:
                return None

            raise

    # --------------------------------------------------------------

    def upload_file(
        self,
        dataset_name: str,
        partition_key: str,
        file_path: Path,
    ) -> bool:

        object_key = self.object_key(
            dataset_name,
            partition_key,
            file_path,
        )

        checksum = self.calculate_md5(
            file_path
        )

        remote_checksum = self.remote_checksum(
            object_key
        )

        if checksum == remote_checksum:

            self.logger.info(
                "Skipping unchanged object: "
                "s3://%s/%s",
                self.bucket,
                object_key,
            )

            return False

        self.logger.info(
            "Uploading %s -> s3://%s/%s",
            file_path,
            self.bucket,
            object_key,
        )

        self.s3_client.upload_file(
            Filename=str(file_path),
            Bucket=self.bucket,
            Key=object_key,
            ExtraArgs={
                "ContentType":
                    "application/octet-stream",
                "Metadata": {
                    "dataset":
                        dataset_name,
                    "partition-date":
                        self.execution_date.isoformat(),
                    "source-md5":
                        checksum,
                    "record-format":
                        "parquet",
                    "pipeline":
                        "airflow-daily",
                },
            },
            Config=self.transfer_config,
        )

        return True

    # --------------------------------------------------------------

    def upload_dataset(
        self,
        dataset_name: str,
        config: dict,
    ) -> tuple[int, int]:

        local_dataset = config[
            "local_dataset"
        ]

        partition_key = config[
            "partition_key"
        ]

        partition_path = self.local_partition(
            local_dataset,
            partition_key,
        )

        if not partition_path.exists():

            raise RuntimeError(
                "Daily partition not found: "
                f"{partition_path}"
            )

        parquet_files = sorted(
            partition_path.glob(
                "*.parquet"
            )
        )

        if not parquet_files:

            raise RuntimeError(
                "No Parquet files found: "
                f"{partition_path}"
            )

        uploaded = 0
        skipped = 0

        for file_path in parquet_files:

            if self.upload_file(
                dataset_name,
                partition_key,
                file_path,
            ):
                uploaded += 1

            else:
                skipped += 1

        return uploaded, skipped

    # --------------------------------------------------------------

    def run(self) -> None:

        self.logger.info(
            "Starting daily S3 upload | "
            "execution_date=%s",
            self.execution_date,
        )

        total_uploaded = 0
        total_skipped = 0

        for (
            dataset_name,
            config,
        ) in self.DATASETS.items():

            self.logger.info(
                "Processing daily dataset: %s",
                dataset_name,
            )

            (
                uploaded,
                skipped,
            ) = self.upload_dataset(
                dataset_name,
                config,
            )

            total_uploaded += uploaded
            total_skipped += skipped

            self.logger.info(
                "Dataset completed: %s | "
                "uploaded=%s | skipped=%s",
                dataset_name,
                uploaded,
                skipped,
            )

        self.logger.info(
            "Daily S3 upload completed | "
            "execution_date=%s | "
            "uploaded=%s | skipped=%s",
            self.execution_date,
            total_uploaded,
            total_skipped,
        )

def parse_arguments() -> argparse.Namespace:
    """
    Parse uploader command-line arguments.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=(
            "historical",
            "daily",
        ),
        default="historical",
    )

    parser.add_argument(
        "--execution-date",
        type=date.fromisoformat,
    )

    arguments = parser.parse_args()

    if (
        arguments.mode == "daily"
        and arguments.execution_date is None
    ):
        parser.error(
            "--execution-date is required "
            "when --mode=daily"
        )

    return arguments


if __name__ == "__main__":

    arguments = parse_arguments()

    if arguments.mode == "daily":

        S3DailyPartitionUploader(
            execution_date=(
                arguments.execution_date
            )
        ).run()

    else:

        S3RawUploader().run()