"""
Project : Enterprise Banking Analytics Platform

File    : fraud_generator.py

Description
-----------
Generates synthetic fraud cases from banking transactions.

Architecture
------------
- list[dict]
- Transaction-driven fraud simulation
- Rule-based risk scoring
- Parquet output through BaseGenerator
"""

from __future__ import annotations

import random

from generators.common.base_generator import BaseGenerator
from generators.common.data_loader import DataLoader
from generators.common.helpers import generate_id, utc_now


# =============================================================================
# Configuration
# =============================================================================

FRAUD_RATE = 0.0075

FRAUD_TYPES = {
    "CARD_NOT_PRESENT": 30,
    "ACCOUNT_TAKEOVER": 20,
    "ATM_FRAUD": 10,
    "TRANSFER_FRAUD": 20,
    "MERCHANT_FRAUD": 10,
    "IDENTITY_THEFT": 10,
}

CASE_STATUSES = [
    "OPEN",
    "INVESTIGATING",
    "CONFIRMED",
    "FALSE_POSITIVE",
    "CLOSED",
]

CASE_STATUS_WEIGHTS = [
    15,
    25,
    25,
    20,
    15,
]


class FraudGenerator(BaseGenerator):
    """
    Generate fraud cases from transactions.
    """

    DATASET_NAME = "fraud"

    FILE_PREFIX = "fraud"

    VALIDATOR = None

    RECORD_SOURCE = "SYNTHETIC_GENERATOR"

    def __init__(self) -> None:
        super().__init__()

        self.loader = DataLoader()

        self.transactions: list[dict] = (
            self.loader.transactions()
        )

        if not self.transactions:
            raise RuntimeError(
                "No transactions found. "
                "Run transaction_generator first."
            )

        self.sequence = 1

        self.batch_id = utc_now().strftime(
            "%Y%m%d%H%M%S"
        )

    # ------------------------------------------------------------------

    @staticmethod
    def should_flag_transaction(
        transaction: dict,
    ) -> bool:
        """
        Determine whether transaction becomes
        a fraud case.
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

        if channel == "ATM":
            probability += 0.003

        if transaction_type == "TRANSFER_OUT":
            probability += 0.010

        if status == "DECLINED":
            probability += 0.020

        return random.random() < min(
            probability,
            0.25,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def fraud_type(
        transaction: dict,
    ) -> str:
        """
        Select context-aware fraud type.
        """

        transaction_type = transaction[
            "transaction_type"
        ]

        channel = transaction[
            "transaction_channel"
        ]

        if transaction_type == "ATM_WITHDRAWAL":
            return "ATM_FRAUD"

        if transaction_type == "TRANSFER_OUT":
            return random.choice(
                [
                    "ACCOUNT_TAKEOVER",
                    "TRANSFER_FRAUD",
                ]
            )

        if (
            transaction_type == "PURCHASE"
            and channel == "POS"
        ):
            return random.choice(
                [
                    "MERCHANT_FRAUD",
                    "IDENTITY_THEFT",
                ]
            )

        fraud_types = list(
            FRAUD_TYPES.keys()
        )

        weights = list(
            FRAUD_TYPES.values()
        )

        return random.choices(
            population=fraud_types,
            weights=weights,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def risk_score(
        transaction: dict,
    ) -> int:
        """
        Calculate transaction fraud risk score.
        """

        score = random.randint(
            20,
            45,
        )

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
            score += 30

        elif amount >= 5_000:
            score += 20

        elif amount >= 2_500:
            score += 10

        if channel == "ONLINE":
            score += 10

        elif channel == "ATM":
            score += 8

        if transaction_type == "TRANSFER_OUT":
            score += 15

        if status == "DECLINED":
            score += 20

        return min(
            score,
            100,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def risk_level(
        score: int,
    ) -> str:
        """
        Derive fraud risk level.
        """

        if score >= 85:
            return "CRITICAL"

        if score >= 70:
            return "HIGH"

        if score >= 50:
            return "MEDIUM"

        return "LOW"

    # ------------------------------------------------------------------

    @staticmethod
    def case_status() -> str:
        """
        Generate fraud case status.
        """

        return random.choices(
            population=CASE_STATUSES,
            weights=CASE_STATUS_WEIGHTS,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    def build_fraud(
        self,
        transaction: dict,
    ) -> dict:
        """
        Build one fraud case.
        """

        fraud_type = self.fraud_type(
            transaction
        )

        score = self.risk_score(
            transaction
        )

        level = self.risk_level(
            score
        )

        status = self.case_status()

        created = utc_now()

        return {
            "fraud_case_id":
                generate_id(
                    "FRD",
                    self.sequence,
                    10,
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
                fraud_type,

            "risk_score":
                score,

            "risk_level":
                level,

            "case_status":
                status,

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
                created,

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
        Generate fraud cases.
        """

        self.logger.info(
            "Starting fraud generation..."
        )

        fraud_count = 0

        transaction_count = 0

        for transaction in self.transactions:

            transaction_count += 1

            if not self.should_flag_transaction(
                transaction
            ):
                continue

            fraud = self.build_fraud(
                transaction
            )

            self.add(fraud)

            self.sequence += 1

            fraud_count += 1

            if fraud_count % 10_000 == 0:
                self.logger.info(
                    "Generated %s fraud cases...",
                    f"{fraud_count:,}",
                )

        actual_fraud_rate = (
            fraud_count / transaction_count
            if transaction_count
            else 0
        )

        self.logger.info(
            "Transactions processed : %s",
            f"{transaction_count:,}",
        )

        self.logger.info(
            "Fraud cases generated : %s",
            f"{fraud_count:,}",
        )

        self.logger.info(
            "Actual fraud rate : %.4f%%",
            actual_fraud_rate * 100,
        )

        self.logger.info(
            "Fraud generation completed."
        )


if __name__ == "__main__":
    FraudGenerator().run()