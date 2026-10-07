"""
Project : Enterprise Banking Analytics Platform

File    : base_generator.py

Description
-----------
Base class for all synthetic data generators.

Provides:
- Record buffering
- Validation
- Batch flushing
- JSON output
- Logging
- Generation statistics
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Any
import pandas as pd

from generators.common.config import RAW_DATA_DIR
from generators.common.logger import get_logger


class BaseGenerator(ABC):
    """
    Base class for synthetic data generators.
    """

    DATASET_NAME: str = ""

    FILE_PREFIX: str = ""

    VALIDATOR = None

    DEFAULT_BATCH_SIZE = 50_000

    def __init__(self) -> None:

        if not self.DATASET_NAME:
            raise ValueError(
                "DATASET_NAME must be defined."
            )

        if not self.FILE_PREFIX:
            raise ValueError(
                "FILE_PREFIX must be defined."
            )

        self.logger = get_logger(
            self.__class__.__name__
        )

        self.records: list[dict[str, Any]] = []

        self.batch_size = self.DEFAULT_BATCH_SIZE

        self.batch_number = 1

        self.total_records = 0

        self.output_directory = (
            Path(RAW_DATA_DIR)
            / self.DATASET_NAME
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ------------------------------------------------------------------
    # Abstract generation method
    # ------------------------------------------------------------------

    @abstractmethod
    def generate(self) -> None:
        """
        Generate dataset records.
        """

        raise NotImplementedError

    # ------------------------------------------------------------------
    # Record handling
    # ------------------------------------------------------------------

    def add(
        self,
        record: dict[str, Any],
    ) -> None:
        """
        Validate and add a record to the buffer.
        """

        self.validate(record)

        self.records.append(record)

        self.total_records += 1

        if len(self.records) >= self.batch_size:
            self.flush()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(
        self,
        record: dict[str, Any],
    ) -> None:
        """
        Execute dataset validator when configured.
        """

        validator = type(self).VALIDATOR

        if validator is None:
            return

        result = validator(record)

        if result is False:
            raise ValueError(
                f"Validation failed for "
                f"{self.DATASET_NAME}: {record}"
            )

    # ------------------------------------------------------------------
    # JSON serialization
    # ------------------------------------------------------------------

    @staticmethod
    def json_serializer(
        value: Any,
    ) -> str:
        """
        Serialize Python objects unsupported by json.
        """

        if isinstance(
            value,
            (datetime, date),
        ):
            return value.isoformat()

        raise TypeError(
            f"Object of type "
            f"{type(value).__name__} "
            f"is not JSON serializable"
        )

    # ------------------------------------------------------------------
    # Batch output
    # ------------------------------------------------------------------

    def batch_file_path(self) -> Path:
        """
        Return Parquet output path for current batch.
        """

        filename = (
            f"{self.FILE_PREFIX}_"
            f"{self.batch_number:05d}.parquet"
        )

        return self.output_directory / filename

    # ------------------------------------------------------------------

    def flush(self) -> None:
        """
        Write buffered records to Parquet.
        """

        if not self.records:
            return

        file_path = self.batch_file_path()

        self.logger.info(
            f"Writing {len(self.records):,} "
            f"records to {file_path}"
        )

        dataframe = pd.DataFrame(
            self.records
        )

        dataframe.to_parquet(
            file_path,
            index=False,
            engine="pyarrow",
        )

        self.records.clear()

        self.batch_number += 1

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Execute the complete generation lifecycle.
        """

        self.logger.info(
            "Starting generator: %s",
            self.DATASET_NAME,
        )

        try:

            self.generate()

            self.flush()

        except Exception:

            self.logger.exception(
                "Generator failed: %s",
                self.DATASET_NAME,
            )

            raise

        self.logger.info(
            "Generator completed: %s",
            self.DATASET_NAME,
        )

        self.logger.info(
            "Total records generated: %d",
            self.total_records,
        )