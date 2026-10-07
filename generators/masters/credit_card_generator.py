"""
Project : Enterprise Banking Analytics Platform

File    : credit_card_generator.py

Description
-----------
Generates synthetic credit card records.

Architecture
------------
- list[dict]
- Customer/account referential integrity
- Credit score driven card eligibility
- Parquet output through BaseGenerator
"""

from __future__ import annotations

import random
from collections import defaultdict
from datetime import date, timedelta

from generators.common.base_generator import BaseGenerator
from generators.common.data_loader import DataLoader
from generators.common.helpers import generate_id, utc_now
from generators.common.validators import validate_credit_card


# =============================================================================
# Configuration
# =============================================================================

CARD_PRODUCTS = {
    "CLASSIC": {
        "minimum_score": 580,
        "credit_limit": (1_000, 5_000),
        "apr": (0.1999, 0.2999),
    },
    "GOLD": {
        "minimum_score": 650,
        "credit_limit": (5_000, 15_000),
        "apr": (0.1599, 0.2599),
    },
    "PLATINUM": {
        "minimum_score": 700,
        "credit_limit": (10_000, 30_000),
        "apr": (0.1299, 0.2199),
    },
    "SIGNATURE": {
        "minimum_score": 760,
        "credit_limit": (25_000, 75_000),
        "apr": (0.0999, 0.1899),
    },
}

CARD_STATUSES = [
    "ACTIVE",
    "BLOCKED",
    "CLOSED",
]

CARD_STATUS_WEIGHTS = [
    97,
    2,
    1,
]

CARD_PROBABILITY = {
    "STUDENT": 0.25,
    "YOUNG_PROFESSIONAL": 0.65,
    "FAMILY": 0.75,
    "AFFLUENT": 0.90,
    "RETIREE": 0.50,
}


# =============================================================================
# Credit Card Generator
# =============================================================================


class CreditCardGenerator(BaseGenerator):

    DATASET_NAME = "credit_cards"

    FILE_PREFIX = "credit_cards"

    VALIDATOR = validate_credit_card

    RECORD_SOURCE = "SYNTHETIC_GENERATOR"

    def __init__(self) -> None:
        super().__init__()

        self.loader = DataLoader()

        self.customers: list[dict] = (
            self.loader.customers()
        )

        self.accounts: list[dict] = (
            self.loader.accounts()
        )

        if not self.customers:
            raise RuntimeError(
                "No customers found. "
                "Run customer_generator first."
            )

        if not self.accounts:
            raise RuntimeError(
                "No accounts found. "
                "Run account_generator first."
            )

        self.accounts_by_customer: dict[
            str,
            list[dict],
        ] = defaultdict(list)

        for account in self.accounts:
            self.accounts_by_customer[
                account["customer_id"]
            ].append(account)

        self.sequence = 1

        self.batch_id = utc_now().strftime(
            "%Y%m%d%H%M%S"
        )

    # ------------------------------------------------------------------

    @staticmethod
    def should_generate_card(
        customer: dict,
    ) -> bool:

        profile = customer.get(
            "profile",
            "YOUNG_PROFESSIONAL",
        )

        probability = CARD_PROBABILITY.get(
            profile,
            0.50,
        )

        return random.random() < probability

    # ------------------------------------------------------------------

    @staticmethod
    def card_product(
        credit_score: int,
    ) -> str:

        eligible_products = [
            product
            for product, configuration
            in CARD_PRODUCTS.items()
            if (
                credit_score
                >= configuration["minimum_score"]
            )
        ]

        if not eligible_products:
            return "CLASSIC"

        return random.choice(
            eligible_products
        )

    # ------------------------------------------------------------------

    @staticmethod
    def card_status() -> str:

        return random.choices(
            population=CARD_STATUSES,
            weights=CARD_STATUS_WEIGHTS,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def credit_limit(
        product: str,
    ) -> float:

        minimum, maximum = (
            CARD_PRODUCTS[
                product
            ]["credit_limit"]
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
    def apr(
        product: str,
    ) -> float:

        minimum, maximum = (
            CARD_PRODUCTS[
                product
            ]["apr"]
        )

        return round(
            random.uniform(
                minimum,
                maximum,
            ),
            4,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def current_balance(
        credit_limit: float,
        status: str,
    ) -> float:

        if status == "CLOSED":
            return 0.00

        utilization = random.uniform(
            0.00,
            0.85,
        )

        return round(
            credit_limit * utilization,
            2,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def issued_date(
        customer: dict,
    ) -> date:

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

        total_days = (
            today - customer_since
        ).days

        return (
            customer_since
            + timedelta(
                days=random.randint(
                    0,
                    total_days,
                )
            )
        )

    # ------------------------------------------------------------------

    @staticmethod
    def card_number(
        sequence: int,
    ) -> str:
        """
        Synthetic non-production card number.
        """

        return f"99990000{sequence:08d}"

    # ------------------------------------------------------------------

    def customer_account(
        self,
        customer_id: str,
    ) -> dict | None:

        accounts = (
            self.accounts_by_customer.get(
                customer_id,
                [],
            )
        )

        eligible_accounts = [
            account
            for account in accounts
            if (
                account["account_status"]
                != "CLOSED"
                and account["account_type"]
                == "CHECKING"
            )
        ]

        if not eligible_accounts:
            return None

        return random.choice(
            eligible_accounts
        )

    # ------------------------------------------------------------------

    def build_card(
        self,
        customer: dict,
    ) -> dict | None:

        account = self.customer_account(
            customer["customer_id"]
        )

        if account is None:
            return None

        credit_score = int(
            customer.get(
                "credit_score",
                650,
            )
        )

        product = self.card_product(
            credit_score
        )

        limit = self.credit_limit(
            product
        )

        status = self.card_status()

        balance = self.current_balance(
            limit,
            status,
        )

        available_credit = round(
            limit - balance,
            2,
        )

        issued = self.issued_date(
            customer
        )

        expiration = (
            issued
            + timedelta(days=365 * 4)
        )

        created = utc_now()

        return {
            "card_id":
                generate_id(
                    "CARD",
                    self.sequence,
                    8,
                ),

            "card_number":
                self.card_number(
                    self.sequence
                ),

            "customer_id":
                customer["customer_id"],

            "account_id":
                account["account_id"],

            "branch_id":
                customer["branch_id"],

            "card_product":
                product,

            "card_status":
                status,

            "credit_limit":
                limit,

            "current_balance":
                balance,

            "available_credit":
                available_credit,

            "apr":
                self.apr(product),

            "issued_date":
                issued,

            "expiration_date":
                expiration,

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

        self.logger.info(
            "Starting credit card generation..."
        )

        card_count = 0

        skipped_customers = 0

        for customer in self.customers:

            if not self.should_generate_card(
                customer
            ):
                continue

            card = self.build_card(
                customer
            )

            if card is None:
                skipped_customers += 1
                continue

            self.add(card)

            self.sequence += 1

            card_count += 1

            if card_count % 10_000 == 0:
                self.logger.info(
                    f"Generated "
                    f"{card_count:,} credit cards..."
                )

        self.logger.info(
            f"Customers processed : "
            f"{len(self.customers):,}"
        )

        self.logger.info(
            f"Credit cards generated : "
            f"{card_count:,}"
        )

        self.logger.info(
            f"Customers skipped : "
            f"{skipped_customers:,}"
        )

        self.logger.info(
            "Credit card generation completed."
        )


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":
    CreditCardGenerator().run()