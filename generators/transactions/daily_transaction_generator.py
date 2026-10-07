"""
Project : Enterprise Banking Analytics Platform

Daily incremental transaction generator.

Designed for Apache Airflow execution-date driven
incremental data generation.
"""

from __future__ import annotations

import argparse
import hashlib
import random
import shutil

from datetime import (
    date,
    datetime,
    time,
    timedelta,
)

import pyarrow as pa
import pyarrow.parquet as pq

from generators.common.config import RAW_DATA_DIR
from generators.common.data_loader import DataLoader


DAILY_MIN_TRANSACTIONS = 1
DAILY_MAX_TRANSACTIONS = 8

BATCH_SIZE = 50_000

TRANSACTION_TYPES = (
    "PURCHASE",
    "ATM_WITHDRAWAL",
    "DEPOSIT",
    "TRANSFER_IN",
    "TRANSFER_OUT",
    "BILL_PAYMENT",
)

TRANSACTION_WEIGHTS = (
    45,
    10,
    8,
    10,
    12,
    15,
)

MERCHANTS = (
    ("Amazon", "ONLINE_RETAIL"),
    ("Walmart", "RETAIL"),
    ("Target", "RETAIL"),
    ("Costco", "WHOLESALE"),
    ("Starbucks", "FOOD_BEVERAGE"),
    ("Uber", "TRANSPORTATION"),
    ("Netflix", "ENTERTAINMENT"),
    ("Shell", "FUEL"),
)


class DailyTransactionGenerator:
    """
    Generate one business day's transactions.
    """

    def __init__(
        self,
        execution_date: date,
    ) -> None:

        self.execution_date = execution_date

        self.loader = DataLoader()

        self.accounts: list[dict] = (
            self.loader.accounts()
        )

        if not self.accounts:
            raise RuntimeError(
                "No accounts found."
            )

        self.output_dir = (
            RAW_DATA_DIR
            / "transactions_daily"
            / (
                "transaction_date="
                f"{execution_date.isoformat()}"
            )
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.records: list[dict] = []

        self.file_sequence = 1

        self.transaction_sequence = 1

        self.batch_id = (
            "TXN_"
            + execution_date.strftime(
                "%Y%m%d"
            )
        )

        # Deterministic execution.
        random.seed(
            int(
                execution_date.strftime(
                    "%Y%m%d"
                )
            )
        )

    # --------------------------------------------------------------

    def transaction_id(
        self,
        account_id: str,
        sequence: int,
    ) -> str:
        """
        Generate deterministic transaction ID.
        """

        source = (
            f"{self.execution_date.isoformat()}"
            f"|{account_id}"
            f"|{sequence}"
        )

        digest = hashlib.sha256(
            source.encode("utf-8")
        ).hexdigest()[:20].upper()

        return f"TXN{digest}"

    # --------------------------------------------------------------

    def transaction_timestamp(
        self,
    ) -> datetime:
        """
        Generate timestamp within execution date.
        """

        seconds = random.randint(
            0,
            86_399,
        )

        start = datetime.combine(
            self.execution_date,
            time.min,
        )

        return start + timedelta(
            seconds=seconds
        )

    # --------------------------------------------------------------

    @staticmethod
    def transaction_amount(
        transaction_type: str,
    ) -> float:

        ranges = {
            "PURCHASE": (
                5,
                2_500,
            ),
            "ATM_WITHDRAWAL": (
                20,
                1_000,
            ),
            "DEPOSIT": (
                100,
                10_000,
            ),
            "TRANSFER_IN": (
                50,
                15_000,
            ),
            "TRANSFER_OUT": (
                50,
                15_000,
            ),
            "BILL_PAYMENT": (
                25,
                5_000,
            ),
        }

        minimum, maximum = ranges[
            transaction_type
        ]

        return round(
            random.uniform(
                minimum,
                maximum,
            ),
            2,
        )

    # --------------------------------------------------------------

    @staticmethod
    def transaction_direction(
        transaction_type: str,
    ) -> str:

        if transaction_type in {
            "DEPOSIT",
            "TRANSFER_IN",
        }:
            return "CREDIT"

        return "DEBIT"

    # --------------------------------------------------------------

    @staticmethod
    def transaction_channel(
        transaction_type: str,
    ) -> str:

        if transaction_type == "PURCHASE":
            return "POS"

        if (
            transaction_type
            == "ATM_WITHDRAWAL"
        ):
            return "ATM"

        return random.choice(
            (
                "MOBILE",
                "ONLINE",
                "BRANCH",
            )
        )

    # --------------------------------------------------------------

    @staticmethod
    def transaction_status() -> str:

        return random.choices(
            population=(
                "COMPLETED",
                "PENDING",
                "DECLINED",
                "REVERSED",
            ),
            weights=(
                92,
                3,
                3,
                2,
            ),
            k=1,
        )[0]

    # --------------------------------------------------------------

    def build_transaction(
        self,
        account: dict,
    ) -> dict:

        transaction_type = random.choices(
            population=TRANSACTION_TYPES,
            weights=TRANSACTION_WEIGHTS,
            k=1,
        )[0]

        channel = self.transaction_channel(
            transaction_type
        )

        merchant_name = None
        merchant_category = None

        if transaction_type == "PURCHASE":

            (
                merchant_name,
                merchant_category,
            ) = random.choice(
                MERCHANTS
            )

        transaction = {
            "transaction_id":
                self.transaction_id(
                    account["account_id"],
                    self.transaction_sequence,
                ),

            "account_id":
                account["account_id"],

            "customer_id":
                account["customer_id"],

            "branch_id":
                account["branch_id"],

            "transaction_type":
                transaction_type,

            "transaction_direction":
                self.transaction_direction(
                    transaction_type
                ),

            "transaction_amount":
                self.transaction_amount(
                    transaction_type
                ),

            "transaction_status":
                self.transaction_status(),

            "transaction_timestamp":
                self.transaction_timestamp(),

            "transaction_channel":
                channel,

            "merchant_name":
                merchant_name,

            "merchant_category":
                merchant_category,

            "transaction_city":
                None,

            "transaction_state":
                None,

            "currency_code":
                account.get(
                    "currency_code",
                    "USD",
                ),

            "batch_id":
                self.batch_id,

            "record_source":
                "DAILY_AIRFLOW_GENERATOR",
        }

        self.transaction_sequence += 1

        return transaction

    # --------------------------------------------------------------

    def flush(self) -> None:
        """
        Write current batch to Parquet.
        """

        if not self.records:
            return

        file_path = (
            self.output_dir
            / (
                "transactions_"
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
            f"records: {file_path}"
        )

        self.records.clear()

        self.file_sequence += 1

    # --------------------------------------------------------------

    def run(self) -> None:

        if self.output_dir.exists():
            shutil.rmtree(
                self.output_dir
            )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(
            "Generating daily transactions "
            f"for {self.execution_date}"
        )

        for account in self.accounts:

            if (
                account.get("account_status")
                != "ACTIVE"
            ):
                continue

            transaction_count = random.randint(
                DAILY_MIN_TRANSACTIONS,
                DAILY_MAX_TRANSACTIONS,
            )

            for _ in range(
                transaction_count
            ):

                self.records.append(
                    self.build_transaction(
                        account
                    )
                )

                if (
                    len(self.records)
                    >= BATCH_SIZE
                ):
                    self.flush()

        self.flush()

        print(
            "Daily transaction generation "
            "completed."
        )

        print(
            "Total records generated: "
            f"{self.transaction_sequence - 1:,}"
        )


def parse_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--execution-date",
        required=True,
        type=date.fromisoformat,
        help="Execution date in YYYY-MM-DD format",
    )

    return parser.parse_args()


if __name__ == "__main__":

    arguments = parse_arguments()

    DailyTransactionGenerator(
        execution_date=(
            arguments.execution_date
        )
    ).run()