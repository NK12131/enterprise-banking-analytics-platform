"""
Project : Enterprise Banking Analytics Platform

File    : transaction_generator.py

Description
-----------
Generates synthetic banking transactions.

Architecture
------------
- list[dict]
- Account/customer referential integrity
- Merchant and transaction behavior simulation
- Chunk-friendly generation
- Parquet output through BaseGenerator
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from generators.common.base_generator import BaseGenerator
from generators.common.data_loader import DataLoader
from generators.common.helpers import generate_id, utc_now
from generators.common.validators import validate_transaction


# =============================================================================
# Configuration
# =============================================================================

TRANSACTIONS_PER_ACCOUNT = (5, 30)

TRANSACTION_TYPES = [
    "PURCHASE",
    "ATM_WITHDRAWAL",
    "DEPOSIT",
    "TRANSFER_IN",
    "TRANSFER_OUT",
    "BILL_PAYMENT",
]

TRANSACTION_TYPE_WEIGHTS = [
    55,
    8,
    8,
    7,
    7,
    15,
]


MERCHANTS = {
    "GROCERY": [
        "Fresh Market",
        "Green Basket",
        "Daily Foods",
        "Family Grocery",
    ],
    "RESTAURANT": [
        "Urban Kitchen",
        "Golden Grill",
        "City Bistro",
        "Sunset Cafe",
    ],
    "RETAIL": [
        "Metro Retail",
        "Value Store",
        "Prime Shopping",
        "Urban Outfit",
    ],
    "FUEL": [
        "Rapid Fuel",
        "City Gas",
        "Highway Energy",
    ],
    "TRAVEL": [
        "Sky Travel",
        "Metro Hotels",
        "City Transport",
    ],
    "HEALTHCARE": [
        "Health Pharmacy",
        "Care Medical",
        "Wellness Clinic",
    ],
    "ENTERTAINMENT": [
        "Digital Media",
        "Cinema World",
        "Stream Entertainment",
    ],
    "UTILITIES": [
        "City Energy",
        "Metro Water",
        "Digital Telecom",
    ],
}


TRANSACTION_AMOUNT_RANGES = {
    "PURCHASE": (
        5.00,
        2_500.00,
    ),
    "ATM_WITHDRAWAL": (
        20.00,
        1_000.00,
    ),
    "DEPOSIT": (
        100.00,
        10_000.00,
    ),
    "TRANSFER_IN": (
        50.00,
        15_000.00,
    ),
    "TRANSFER_OUT": (
        50.00,
        15_000.00,
    ),
    "BILL_PAYMENT": (
        25.00,
        5_000.00,
    ),
}


TRANSACTION_STATUSES = [
    "COMPLETED",
    "PENDING",
    "DECLINED",
    "REVERSED",
]

TRANSACTION_STATUS_WEIGHTS = [
    96,
    1,
    2,
    1,
]


CHANNELS = [
    "MOBILE",
    "ONLINE",
    "ATM",
    "BRANCH",
    "POS",
]


# =============================================================================
# Transaction Generator
# =============================================================================


class TransactionGenerator(BaseGenerator):
    """
    Generate synthetic banking transactions.
    """

    DATASET_NAME = "transactions"

    FILE_PREFIX = "transactions"

    VALIDATOR = validate_transaction

    RECORD_SOURCE = "SYNTHETIC_GENERATOR"

    def __init__(self) -> None:
        super().__init__()

        self.loader = DataLoader()

        self.accounts: list[dict] = (
            self.loader.accounts()
        )

        if not self.accounts:
            raise RuntimeError(
                "No account records found. "
                "Run account_generator first."
            )

        self.sequence = 1

        self.batch_id = utc_now().strftime(
            "%Y%m%d%H%M%S"
        )

    # ------------------------------------------------------------------

    @staticmethod
    def transaction_type() -> str:
        """
        Select transaction type.
        """

        return random.choices(
            population=TRANSACTION_TYPES,
            weights=TRANSACTION_TYPE_WEIGHTS,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def transaction_status() -> str:
        """
        Select transaction status.
        """

        return random.choices(
            population=TRANSACTION_STATUSES,
            weights=TRANSACTION_STATUS_WEIGHTS,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def transaction_amount(
        transaction_type: str,
    ) -> float:
        """
        Generate transaction amount.
        """

        minimum, maximum = (
            TRANSACTION_AMOUNT_RANGES[
                transaction_type
            ]
        )

        return round(
            random.uniform(
                minimum,
                maximum,
            ),
            2,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def transaction_timestamp() -> datetime:
        """
        Generate transaction timestamp.
        """

        now = utc_now()

        return (
            now
            - timedelta(
                seconds=random.randint(
                    0,
                    365 * 24 * 60 * 60,
                )
            )
        )

    # ------------------------------------------------------------------

    @staticmethod
    def transaction_channel(
        transaction_type: str,
    ) -> str:
        """
        Resolve transaction channel.
        """

        if transaction_type == "ATM_WITHDRAWAL":
            return "ATM"

        if transaction_type == "PURCHASE":
            return "POS"

        if transaction_type == "DEPOSIT":
            return random.choice(
                [
                    "BRANCH",
                    "MOBILE",
                    "ATM",
                ]
            )

        if transaction_type in {
            "TRANSFER_IN",
            "TRANSFER_OUT",
            "BILL_PAYMENT",
        }:
            return random.choice(
                [
                    "MOBILE",
                    "ONLINE",
                ]
            )

        return random.choice(CHANNELS)

    # ------------------------------------------------------------------

    @staticmethod
    def merchant_details(
        transaction_type: str,
    ) -> tuple[str | None, str | None]:
        """
        Generate merchant details for purchase transactions.
        """

        if transaction_type != "PURCHASE":
            return None, None

        category = random.choice(
            list(MERCHANTS.keys())
        )

        merchant = random.choice(
            MERCHANTS[category]
        )

        return merchant, category

    # ------------------------------------------------------------------

    @staticmethod
    def transaction_direction(
        transaction_type: str,
    ) -> str:
        """
        Resolve debit or credit direction.
        """

        if transaction_type in {
            "DEPOSIT",
            "TRANSFER_IN",
        }:
            return "CREDIT"

        return "DEBIT"

    # ------------------------------------------------------------------

    @staticmethod
    def location(
        channel: str,
    ) -> tuple[str | None, str | None]:
        """
        Generate transaction location.
        """

        if channel in {
            "MOBILE",
            "ONLINE",
        }:
            return None, None

        cities = [
            ("Houston", "TX"),
            ("Dallas", "TX"),
            ("Austin", "TX"),
            ("New York", "NY"),
            ("Chicago", "IL"),
            ("Atlanta", "GA"),
            ("Phoenix", "AZ"),
            ("Los Angeles", "CA"),
        ]

        return random.choice(cities)

    # ------------------------------------------------------------------

    def build_transaction(
        self,
        account: dict,
    ) -> dict:
        """
        Build one transaction record.
        """

        transaction_type = (
            self.transaction_type()
        )

        status = self.transaction_status()

        amount = self.transaction_amount(
            transaction_type
        )

        channel = self.transaction_channel(
            transaction_type
        )

        merchant_name, merchant_category = (
            self.merchant_details(
                transaction_type
            )
        )

        direction = self.transaction_direction(
            transaction_type
        )

        city, state = self.location(
            channel
        )

        transaction_time = (
            self.transaction_timestamp()
        )

        created = utc_now()

        return {
            "transaction_id":
                generate_id(
                    "TXN",
                    self.sequence,
                    12,
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
                direction,

            "transaction_amount":
                amount,

            "transaction_status":
                status,

            "transaction_timestamp":
                transaction_time,

            "transaction_channel":
                channel,

            "merchant_name":
                merchant_name,

            "merchant_category":
                merchant_category,

            "transaction_city":
                city,

            "transaction_state":
                state,

            "currency_code":
                "USD",

            "created_timestamp":
                created,

            "updated_timestamp":
                created,

            "batch_id":
                self.batch_id,

            "record_source":
                self.RECORD_SOURCE,
        }

    # ------------------------------------------------------------------

    def generate(self) -> None:
        """
        Generate transactions for active accounts.
        """

        self.logger.info(
            "Starting transaction generation..."
        )

        transaction_count = 0

        accounts_processed = 0

        for account in self.accounts:

            if (
                account["account_status"]
                == "CLOSED"
            ):
                continue

            accounts_processed += 1

            transaction_volume = random.randint(
                *TRANSACTIONS_PER_ACCOUNT
            )

            for _ in range(
                transaction_volume
            ):

                transaction = (
                    self.build_transaction(
                        account
                    )
                )

                self.add(
                    transaction
                )

                self.sequence += 1

                transaction_count += 1

                if (
                    transaction_count
                    % 100_000
                    == 0
                ):
                    self.logger.info(
                        "Generated %s transactions...",
                        f"{transaction_count:,}",
                    )

        self.logger.info(
            "Accounts processed : %s",
            f"{accounts_processed:,}",
        )

        self.logger.info(
            "Transactions generated : %s",
            f"{transaction_count:,}",
        )

        self.logger.info(
            "Transaction generation completed."
        )


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":
    TransactionGenerator().run()