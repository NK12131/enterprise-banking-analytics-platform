"""
Project : Enterprise Banking Analytics Platform

File    : data_loader.py

Description
-----------
Loads generated datasets as list[dict].
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from generators.common.config import RAW_DATA_DIR


logger = logging.getLogger(__name__)


class DataLoader:
    """
    Load generated datasets.

    All public loader methods return list[dict].
    """

    def __init__(self) -> None:
        self.raw_data_dir = Path(RAW_DATA_DIR)

    # ------------------------------------------------------------------

    def load_csv_dataset(
        self,
        dataset_name: str,
    ) -> list[dict[str, Any]]:
        """
        Load CSV dataset and return list of dictionaries.
        """

        logger.info(
            "Loading CSV dataset: %s",
            dataset_name,
        )

        dataset_path = (
            self.raw_data_dir
            / dataset_name
        )

        files = sorted(
            dataset_path.glob("*.csv")
        )

        if not files:
            logger.warning(
                "No CSV files found for dataset: %s",
                dataset_name,
            )
            return []

        records: list[dict[str, Any]] = []

        for file_path in files:

            logger.debug(
                "Reading CSV file: %s",
                file_path,
            )

            dataframe = pd.read_csv(
                file_path
            )

            records.extend(
                dataframe.to_dict(
                    orient="records"
                )
            )

        logger.info(
            "Loaded %d records from dataset: %s",
            len(records),
            dataset_name,
        )

        return records

    # ------------------------------------------------------------------

    def load_parquet_dataset(
    self,
    dataset_name: str,
) -> list[dict]:
        """
        Load Parquet dataset as list[dict].
        """

        dataset_path = (
            self.raw_data_dir
            / dataset_name
        )

        logger.info(
            "Loading Parquet dataset: %s",
            dataset_name,
        )

        logger.info(
            "Dataset directory: %s",
            dataset_path.resolve(),
        )

        files = sorted(
            dataset_path.glob("*.parquet")
        )

        logger.info(
            "Parquet files found: %d",
            len(files),
        )

        if not files:
            logger.warning(
                "No Parquet files found in: %s",
                dataset_path.resolve(),
            )
            return []

        records = []

        for file_path in files:

            logger.info(
                "Reading Parquet file: %s",
                file_path,
            )

            dataframe = pd.read_parquet(
                file_path
            )

            records.extend(
                dataframe.to_dict(
                    orient="records"
                )
            )

        logger.info(
            "Loaded %d records from dataset: %s",
            len(records),
            dataset_name,
        )

        return records

    # ------------------------------------------------------------------
    # Reference datasets
    # ------------------------------------------------------------------

    def branches(self) -> list[dict]:
        return self.load_parquet_dataset(
            "branches"
        )

    def employees(self) -> list[dict]:
        return self.load_parquet_dataset(
            "employees"
        )

    # ------------------------------------------------------------------
    # Master datasets
    # ------------------------------------------------------------------

    def customers(self) -> list[dict]:
        return self.load_parquet_dataset(
            "customers"
        )

    def accounts(self) -> list[dict]:
        return self.load_parquet_dataset(
            "accounts"
        )

    def loans(self) -> list[dict]:
        return self.load_parquet_dataset(
            "loans"
        )

    def credit_cards(self) -> list[dict]:
        return self.load_parquet_dataset(
            "credit_cards"
        )

    # ------------------------------------------------------------------
    # Transaction datasets
    # ------------------------------------------------------------------

    def transactions(self) -> list[dict]:
        return self.load_parquet_dataset(
            "transactions"
        )

    def fraud(self) -> list[dict]:
        return self.load_parquet_dataset(
            "fraud"
        )