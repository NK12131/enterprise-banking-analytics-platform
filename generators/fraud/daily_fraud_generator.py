"""
Project : Enterprise Banking Analytics Platform

Daily incremental fraud generator.

Reads one execution-date transaction partition and
generates deterministic fraud cases for Airflow.
"""

from __future__ import annotations

import argparse
import hashlib
import random
import shutil

from datetime import date, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from generators.common.config import RAW_DATA_DIR


FRAUD_RATE = 0.0075

BATCH_SIZE = 50_000


class DailyFraudGenerator:
    """
    Generate fraud cases for one transaction date.
    """

    def __init__(
        self,
        execution_date: date,
    ) -> None:

        self.execution_date = execution_date

        self.transaction_dir = (
            Path(RAW_DATA_DIR)
            / "transactions_daily"
            / (
                "transaction_date="
                f"{execution_date.isoformat()}"
            )
        )

        self.output_dir = (
            Path(RAW_DATA_DIR)
            / "fraud_daily"
            / (
                "detection_date="
                f"{execution_date.isoformat()}"
            )
        )

        self.records: list[dict] = []

        self.file_sequence = 1

        self.fraud_sequence = 1

        self.batch_id = (
            "FRD_"
            + execution_date.strftime(
                "%Y%m%d"
            )
        )

        random.seed(
            int(
                execution_date.strftime(
                    "%Y%m%d"
                )
            )
            + 1000
        )

    # --------------------------------------------------------------

    def fraud_case_id(
        self,
        transaction_id: str,
    ) -> str:
        """
        Generate deterministic fraud case ID.
        """

        source = (
            f"{self.execution_date.isoformat()}"
            f"|{transaction_id}"
            "|FRAUD"
        )

        digest = hashlib.sha256(
            source.encode("utf-8")
        ).hexdigest()[:20].upper()

        return f"FRD{digest}"

    # --------------------------------------------------------------

    @staticmethod
    def fraud_probability(
        transaction: dict,
    ) -> float:
        """
        Calculate transaction fraud probability.
        """

        probability = FRAUD_RATE

        amount = float(
            transaction["transaction_amount"]
        )

        channel = transaction[
            "transaction_channel"
        ]

        transaction_type = transaction[
            "transaction_type"
        ]

        status = transaction[
            "transaction_status"
        ]

        if amount >= 10_000:
            probability += 0.025

        elif amount >= 5_000:
            probability += 0.010

        if channel == "ONLINE":
            probability += 0.004

        elif channel == "ATM":
            probability += 0.003

        if transaction_type == "TRANSFER_OUT":
            probability += 0.010

        if status == "DECLINED":
            probability += 0.020

        return min(
            probability,
            0.25,
        )

    # --------------------------------------------------------------

    def is_fraud(
        self,
        transaction: dict,
    ) -> bool:

        return (
            random.random()
            < self.fraud_probability(
                transaction
            )
        )

    # --------------------------------------------------------------

    @staticmethod
    def fraud_type(
        transaction: dict,
    ) -> str:

        transaction_type = transaction[
            "transaction_type"
        ]

        channel = transaction[
            "transaction_channel"
        ]

        if (
            transaction_type
            == "ATM_WITHDRAWAL"
        ):
            return "ATM_FRAUD"

        if transaction_type == "TRANSFER_OUT":

            return random.choice(
                (
                    "ACCOUNT_TAKEOVER",
                    "TRANSFER_FRAUD",
                )
            )

        if (
            transaction_type == "PURCHASE"
            and channel == "POS"
        ):

            return random.choice(
                (
                    "MERCHANT_FRAUD",
                    "IDENTITY_THEFT",
                )
            )

        return random.choice(
            (
                "CARD_NOT_PRESENT",
                "ACCOUNT_TAKEOVER",
                "IDENTITY_THEFT",
            )
        )

    # --------------------------------------------------------------

    @staticmethod
    def risk_score(
        transaction: dict,
    ) -> int:

        score = random.randint(
            20,
            45,
        )

        amount = float(
            transaction["transaction_amount"]
        )

        if amount >= 10_000:
            score += 30

        elif amount >= 5_000:
            score += 20

        elif amount >= 2_500:
            score += 10

        if (
            transaction["transaction_channel"]
            == "ONLINE"
        ):
            score += 10

        elif (
            transaction["transaction_channel"]
            == "ATM"
        ):
            score += 8

        if (
            transaction["transaction_type"]
            == "TRANSFER_OUT"
        ):
            score += 15

        if (
            transaction["transaction_status"]
            == "DECLINED"
        ):
            score += 20

        return min(
            score,
            100,
        )

    # --------------------------------------------------------------

    @staticmethod
    def risk_level(
        score: int,
    ) -> str:

        if score >= 85:
            return "CRITICAL"

        if score >= 70:
            return "HIGH"

        if score >= 50:
            return "MEDIUM"

        return "LOW"

    # --------------------------------------------------------------

    @staticmethod
    def case_status() -> str:

        return random.choices(
            population=(
                "OPEN",
                "INVESTIGATING",
                "CONFIRMED",
                "FALSE_POSITIVE",
                "CLOSED",
            ),
            weights=(
                15,
                25,
                25,
                20,
                15,
            ),
            k=1,
        )[0]

    # --------------------------------------------------------------

    def build_fraud(
        self,
        transaction: dict,
    ) -> dict:

        score = self.risk_score(
            transaction
        )

        detected_timestamp = datetime.combine(
            self.execution_date,
            datetime.min.time(),
        )

        return {
            "fraud_case_id":
                self.fraud_case_id(
                    transaction[
                        "transaction_id"
                    ]
                ),

            "transaction_id":
                transaction["transaction_id"],

            "account_id":
                transaction["account_id"],

            "customer_id":
                transaction["customer_id"],

            "branch_id":
                transaction["branch_id"],

            "fraud_type":
                self.fraud_type(
                    transaction
                ),

            "risk_score":
                score,

            "risk_level":
                self.risk_level(
                    score
                ),

            "case_status":
                self.case_status(),

            "transaction_amount":
                transaction[
                    "transaction_amount"
                ],

            "transaction_type":
                transaction[
                    "transaction_type"
                ],

            "transaction_channel":
                transaction[
                    "transaction_channel"
                ],

            "transaction_timestamp":
                transaction[
                    "transaction_timestamp"
                ],

            "merchant_name":
                transaction.get(
                    "merchant_name"
                ),

            "merchant_category":
                transaction.get(
                    "merchant_category"
                ),

            "detected_timestamp":
                detected_timestamp,

            "batch_id":
                self.batch_id,

            "record_source":
                "DAILY_AIRFLOW_GENERATOR",
        }

    # --------------------------------------------------------------

    def flush(self) -> None:

        if not self.records:
            return

        file_path = (
            self.output_dir
            / (
                "fraud_"
                f"{self.execution_date:%Y%m%d}_"
                f"{self.file_sequence:05d}"
                ".parquet"
            )
        )

        table = pa.Table.from_pylist(
            self.records
        )

        pq.write_table(
            table,
            file_path,
            compression="snappy",
        )

        print(
            f"Wrote {len(self.records):,} "
            f"fraud records: {file_path}"
        )

        self.records.clear()

        self.file_sequence += 1

    # --------------------------------------------------------------

    def run(self) -> None:

        if not self.transaction_dir.exists():

            raise RuntimeError(
                "Transaction partition not found: "
                f"{self.transaction_dir}"
            )

        parquet_files = list(
            self.transaction_dir.glob(
                "*.parquet"
            )
        )

        if not parquet_files:

            raise RuntimeError(
                "No transaction Parquet files found: "
                f"{self.transaction_dir}"
            )

        if self.output_dir.exists():

            shutil.rmtree(
                self.output_dir
            )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(
            "Generating daily fraud for "
            f"{self.execution_date}"
        )

        transaction_dataset = ds.dataset(
            self.transaction_dir,
            format="parquet",
        )

        scanner = transaction_dataset.scanner(
            batch_size=100_000,
        )

        transaction_count = 0

        fraud_count = 0

        for batch in scanner.to_batches():

            transactions = (
                batch.to_pylist()
            )

            for transaction in transactions:

                transaction_count += 1

                if not self.is_fraud(
                    transaction
                ):
                    continue

                self.records.append(
                    self.build_fraud(
                        transaction
                    )
                )

                self.fraud_sequence += 1

                fraud_count += 1

                if (
                    len(self.records)
                    >= BATCH_SIZE
                ):
                    self.flush()

        self.flush()

        fraud_rate = (
            fraud_count / transaction_count
            if transaction_count
            else 0
        )

        print(
            "Transactions processed: "
            f"{transaction_count:,}"
        )

        print(
            "Fraud cases generated: "
            f"{fraud_count:,}"
        )

        print(
            "Fraud rate: "
            f"{fraud_rate:.4%}"
        )

        print(
            "Daily fraud generation completed."
        )


def parse_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--execution-date",
        required=True,
        type=date.fromisoformat,
        help=(
            "Airflow execution date "
            "in YYYY-MM-DD format"
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":

    arguments = parse_arguments()

    DailyFraudGenerator(
        execution_date=(
            arguments.execution_date
        )
    ).run()