"""
Project : Enterprise Banking Analytics Platform

File    : account_generator.py

Description
-----------
Generates synthetic banking accounts for customers.

Architecture
------------
- list[dict]
- Customer profile driven
- Referential integrity with customers
- Parquet output through BaseGenerator
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from generators.common.base_generator import BaseGenerator
from generators.common.data_loader import DataLoader
from generators.common.helpers import generate_id, utc_now
from generators.common.validators import validate_account


# =============================================================================
# Configuration
# =============================================================================

ACCOUNT_TYPES = {
    "CHECKING": {
        "minimum_balance": 100.00,
        "maximum_balance": 25_000.00,
        "interest_rate": 0.00,
    },
    "SAVINGS": {
        "minimum_balance": 500.00,
        "maximum_balance": 100_000.00,
        "interest_rate": 0.035,
    },
    "MONEY_MARKET": {
        "minimum_balance": 5_000.00,
        "maximum_balance": 250_000.00,
        "interest_rate": 0.045,
    },
}

PROFILE_ACCOUNTS = {
    "STUDENT": [
        "CHECKING",
    ],
    "YOUNG_PROFESSIONAL": [
        "CHECKING",
        "SAVINGS",
    ],
    "FAMILY": [
        "CHECKING",
        "SAVINGS",
    ],
    "AFFLUENT": [
        "CHECKING",
        "SAVINGS",
        "MONEY_MARKET",
    ],
    "RETIREE": [
        "CHECKING",
        "SAVINGS",
        "MONEY_MARKET",
    ],
}

ACCOUNT_STATUS = [
    "ACTIVE",
    "DORMANT",
    "CLOSED",
]

ACCOUNT_STATUS_WEIGHTS = [
    96,
    3,
    1,
]


# =============================================================================
# Account Generator
# =============================================================================


class AccountGenerator(BaseGenerator):
    """
    Generate customer bank accounts.
    """

    DATASET_NAME = "accounts"

    FILE_PREFIX = "accounts"

    VALIDATOR = validate_account

    RECORD_SOURCE = "SYNTHETIC_GENERATOR"

    def __init__(self) -> None:
        super().__init__()

        self.loader = DataLoader()

        self.customers: list[dict] = (
            self.loader.customers()
        )

        if not self.customers:
            raise RuntimeError(
                "No customer records found. "
                "Run customer_generator first."
            )

        self.sequence = 1

        self.batch_id = utc_now().strftime(
            "%Y%m%d%H%M%S"
        )

    # ------------------------------------------------------------------

    @staticmethod
    def account_types(
        customer: dict,
    ) -> list[str]:
        """
        Resolve account products from customer profile.
        """

        profile = customer.get(
            "profile",
            "YOUNG_PROFESSIONAL",
        )

        accounts = PROFILE_ACCOUNTS.get(
            profile,
            [
                "CHECKING",
                "SAVINGS",
            ],
        )

        return list(accounts)

    # ------------------------------------------------------------------

    @staticmethod
    def account_status() -> str:
        """
        Generate account status.
        """

        return random.choices(
            population=ACCOUNT_STATUS,
            weights=ACCOUNT_STATUS_WEIGHTS,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def opened_date(
        customer: dict,
    ) -> date:
        """
        Generate account opening date.
        """

        customer_since = customer[
            "customer_since"
        ]

        if isinstance(customer_since, str):
            customer_since = date.fromisoformat(
                customer_since
            )

        today = utc_now().date()

        if customer_since >= today:
            return today

        days = (
            today - customer_since
        ).days

        return (
            customer_since
            + timedelta(
                days=random.randint(
                    0,
                    days,
                )
            )
        )

    # ------------------------------------------------------------------

    @staticmethod
    def closed_date(
        status: str,
        opened_date: date,
    ) -> date | None:
        """
        Generate account closure date.
        """

        if status != "CLOSED":
            return None

        today = utc_now().date()

        earliest = (
            opened_date
            + timedelta(days=30)
        )

        if earliest >= today:
            return today

        days = (
            today - earliest
        ).days

        return (
            earliest
            + timedelta(
                days=random.randint(
                    0,
                    days,
                )
            )
        )

    # ------------------------------------------------------------------

    @staticmethod
    def account_balance(
        account_type: str,
    ) -> float:
        """
        Generate account balance.
        """

        product = ACCOUNT_TYPES[
            account_type
        ]

        return round(
            random.uniform(
                product["minimum_balance"],
                product["maximum_balance"],
            ),
            2,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def interest_rate(
        account_type: str,
    ) -> float:
        """
        Return account interest rate.
        """

        return ACCOUNT_TYPES[
            account_type
        ]["interest_rate"]

    # ------------------------------------------------------------------

    @staticmethod
    def account_number(
        sequence: int,
    ) -> str:
        """
        Generate deterministic account number.
        """

        return (
            f"1001{sequence:012d}"
        )

    # ------------------------------------------------------------------

    def build_account(
        self,
        customer: dict,
        account_type: str,
    ) -> dict:
        """
        Build one account record.
        """

        status = self.account_status()

        opened = self.opened_date(
            customer
        )

        closed = self.closed_date(
            status,
            opened,
        )

        balance = self.account_balance(
            account_type
        )

        if status == "CLOSED":
            balance = 0.00

        created = utc_now()

        return {
            "account_id":
                generate_id(
                    "ACC",
                    self.sequence,
                    8,
                ),

            "account_number":
                self.account_number(
                    self.sequence
                ),

            "customer_id":
                customer["customer_id"],

            "branch_id":
                customer["branch_id"],

            "branch_code":
                customer["branch_code"],

            "account_type":
                account_type,

            "account_status":
                status,

            "currency_code":
                "USD",

            "current_balance":
                balance,

            "available_balance":
                balance,

            "interest_rate":
                self.interest_rate(
                    account_type
                ),

            "opened_date":
                opened,

            "closed_date":
                closed,

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
        Generate accounts for all customers.
        """

        self.logger.info(
            "Generating customer accounts..."
        )

        account_count = 0

        for customer in self.customers:

            account_types = self.account_types(
                customer
            )

            for account_type in account_types:

                account = self.build_account(
                    customer,
                    account_type,
                )

                self.add(account)

                self.sequence += 1

                account_count += 1

                if account_count % 50_000 == 0:
                    self.logger.info(
                        f"Generated "
                        f"{account_count:,} accounts..."
                    )

        self.logger.info(
            f"Customers processed : "
            f"{len(self.customers):,}"
        )

        self.logger.info(
            f"Accounts generated : "
            f"{account_count:,}"
        )

        self.logger.info(
            "Account generation completed."
        )


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":
    AccountGenerator().run()