"""
Validate Airflow daily Parquet partitions.
"""

from __future__ import annotations

import argparse

from datetime import date
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.dataset as ds

from generators.common.config import RAW_DATA_DIR


class DailyParquetValidator:

    def __init__(
        self,
        execution_date: date,
    ) -> None:

        self.execution_date = execution_date

        self.raw_dir = Path(
            RAW_DATA_DIR
        )

    def validate_transactions(
        self,
    ) -> None:

        path = (
            self.raw_dir
            / "transactions_daily"
            / (
                "transaction_date="
                f"{self.execution_date}"
            )
        )

        dataset = ds.dataset(
            path,
            format="parquet",
        )

        scanner = dataset.scanner(
            columns=[
                "transaction_id",
                "transaction_amount",
                "transaction_timestamp",
            ],
            batch_size=100_000,
        )

        row_count = 0
        invalid_amounts = 0
        null_ids = 0
        null_timestamps = 0

        for batch in scanner.to_batches():

            row_count += batch.num_rows

            null_ids += (
                batch["transaction_id"]
                .null_count
            )

            null_timestamps += (
                batch["transaction_timestamp"]
                .null_count
            )

            invalid = pc.less_equal(
                batch["transaction_amount"],
                0,
            )

            invalid_amounts += (
                pc.sum(
                    pc.cast(
                        invalid,
                        "int64",
                    )
                ).as_py()
                or 0
            )

        if row_count <= 0:
            raise RuntimeError(
                "Daily transactions are empty."
            )

        if null_ids:
            raise RuntimeError(
                f"Null transaction IDs: "
                f"{null_ids:,}"
            )

        if null_timestamps:
            raise RuntimeError(
                "Null transaction timestamps: "
                f"{null_timestamps:,}"
            )

        if invalid_amounts:
            raise RuntimeError(
                "Invalid transaction amounts: "
                f"{invalid_amounts:,}"
            )

        print(
            "[PASS] Daily transactions | "
            f"rows={row_count:,}"
        )

    def validate_fraud(
        self,
    ) -> None:

        path = (
            self.raw_dir
            / "fraud_daily"
            / (
                "detection_date="
                f"{self.execution_date}"
            )
        )

        dataset = ds.dataset(
            path,
            format="parquet",
        )

        table = dataset.to_table(
            columns=[
                "fraud_case_id",
                "risk_score",
            ]
        )

        if table.num_rows <= 0:
            raise RuntimeError(
                "Daily fraud dataset is empty."
            )

        if (
            table["fraud_case_id"]
            .null_count
        ):
            raise RuntimeError(
                "Daily fraud contains null IDs."
            )

        invalid_scores = pc.or_(
            pc.less(
                table["risk_score"],
                0,
            ),
            pc.greater(
                table["risk_score"],
                100,
            ),
        )

        invalid_count = (
            pc.sum(
                pc.cast(
                    invalid_scores,
                    "int64",
                )
            ).as_py()
            or 0
        )

        if invalid_count:
            raise RuntimeError(
                "Invalid fraud risk scores: "
                f"{invalid_count:,}"
            )

        print(
            "[PASS] Daily fraud | "
            f"rows={table.num_rows:,}"
        )

    def run(self) -> None:
        """Run all daily Parquet validation checks."""

        self.validate_transactions()

        self.validate_fraud()

        print(
            "[PASS] Daily Parquet audit completed."
        )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the validator."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--execution-date",
        required=True,
        type=date.fromisoformat,
    )

    return parser.parse_args()


if __name__ == "__main__":

    arguments = parse_arguments()

    DailyParquetValidator(
        arguments.execution_date
    ).run()