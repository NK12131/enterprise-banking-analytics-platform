"""
Project : Enterprise Banking Analytics Platform

File    : loan_generator.py

Description
-----------
Generates synthetic banking loan records.

Architecture
------------
- list[dict]
- Customer and account referential integrity
- Customer profile and credit score driven
- Parquet output through BaseGenerator
"""

from __future__ import annotations

import random
from collections import defaultdict
from datetime import date, timedelta

from generators.common.base_generator import BaseGenerator
from generators.common.data_loader import DataLoader
from generators.common.helpers import generate_id, utc_now
from generators.common.validators import validate_loan


# =============================================================================
# Configuration
# =============================================================================

LOAN_TYPES = {
    "PERSONAL_LOAN": {
        "minimum_amount": 2_000,
        "maximum_amount": 50_000,
        "terms": [12, 24, 36, 48, 60],
        "base_rate": 0.085,
    },
    "AUTO_LOAN": {
        "minimum_amount": 10_000,
        "maximum_amount": 80_000,
        "terms": [36, 48, 60, 72],
        "base_rate": 0.065,
    },
    "MORTGAGE": {
        "minimum_amount": 100_000,
        "maximum_amount": 750_000,
        "terms": [180, 240, 360],
        "base_rate": 0.0625,
    },
    "HOME_EQUITY": {
        "minimum_amount": 20_000,
        "maximum_amount": 250_000,
        "terms": [60, 120, 180],
        "base_rate": 0.075,
    },
}


PROFILE_LOANS = {
    "STUDENT": [
        "PERSONAL_LOAN",
    ],
    "YOUNG_PROFESSIONAL": [
        "PERSONAL_LOAN",
        "AUTO_LOAN",
    ],
    "FAMILY": [
        "PERSONAL_LOAN",
        "AUTO_LOAN",
        "MORTGAGE",
    ],
    "AFFLUENT": [
        "AUTO_LOAN",
        "MORTGAGE",
        "HOME_EQUITY",
    ],
    "RETIREE": [
        "PERSONAL_LOAN",
        "HOME_EQUITY",
    ],
}


LOAN_PROBABILITY = {
    "STUDENT": 0.15,
    "YOUNG_PROFESSIONAL": 0.35,
    "FAMILY": 0.55,
    "AFFLUENT": 0.60,
    "RETIREE": 0.25,
}


LOAN_STATUSES = [
    "ACTIVE",
    "PAID_OFF",
    "DELINQUENT",
    "DEFAULTED",
]

LOAN_STATUS_WEIGHTS = [
    82,
    12,
    4,
    2,
]


# =============================================================================
# Loan Generator
# =============================================================================


class LoanGenerator(BaseGenerator):

    DATASET_NAME = "loans"

    FILE_PREFIX = "loans"

    VALIDATOR = validate_loan

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

    def customer_accounts(
        self,
        customer_id: str,
    ) -> list[dict]:
        """
        Return accounts belonging to customer.
        """

        return self.accounts_by_customer.get(
            customer_id,
            [],
        )

    # ------------------------------------------------------------------

    @staticmethod
    def should_generate_loan(
        customer: dict,
    ) -> bool:
        """
        Determine whether customer receives a loan.
        """

        profile = customer.get(
            "profile",
            "YOUNG_PROFESSIONAL",
        )

        probability = LOAN_PROBABILITY.get(
            profile,
            0.30,
        )

        return random.random() < probability

    # ------------------------------------------------------------------

    @staticmethod
    def choose_loan_type(
        customer: dict,
    ) -> str:
        """
        Select loan type from customer profile.
        """

        profile = customer.get(
            "profile",
            "YOUNG_PROFESSIONAL",
        )

        loan_types = PROFILE_LOANS.get(
            profile,
            ["PERSONAL_LOAN"],
        )

        return random.choice(
            loan_types
        )

    # ------------------------------------------------------------------

    @staticmethod
    def loan_amount(
        loan_type: str,
        customer: dict,
    ) -> float:
        """
        Generate loan amount.
        """

        configuration = LOAN_TYPES[
            loan_type
        ]

        minimum = configuration[
            "minimum_amount"
        ]

        maximum = configuration[
            "maximum_amount"
        ]

        annual_income = float(
            customer.get(
                "annual_income",
                50_000,
            )
        )

        if loan_type == "MORTGAGE":
            maximum = min(
                maximum,
                annual_income * 5,
            )

        elif loan_type == "AUTO_LOAN":
            maximum = min(
                maximum,
                annual_income,
            )

        else:
            maximum = min(
                maximum,
                annual_income * 0.75,
            )

        maximum = max(
            minimum,
            maximum,
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
    def interest_rate(
        loan_type: str,
        credit_score: int,
    ) -> float:
        """
        Generate risk-adjusted interest rate.
        """

        base_rate = LOAN_TYPES[
            loan_type
        ]["base_rate"]

        if credit_score >= 760:
            adjustment = -0.010

        elif credit_score >= 700:
            adjustment = 0.000

        elif credit_score >= 650:
            adjustment = 0.015

        elif credit_score >= 600:
            adjustment = 0.030

        else:
            adjustment = 0.050

        return round(
            max(
                0.01,
                base_rate + adjustment,
            ),
            4,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def loan_term(
        loan_type: str,
    ) -> int:
        """
        Select loan term in months.
        """

        return random.choice(
            LOAN_TYPES[
                loan_type
            ]["terms"]
        )

    # ------------------------------------------------------------------

    @staticmethod
    def loan_status() -> str:
        """
        Generate loan status.
        """

        return random.choices(
            population=LOAN_STATUSES,
            weights=LOAN_STATUS_WEIGHTS,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def origination_date(
        customer: dict,
    ) -> date:
        """
        Generate loan origination date.
        """

        customer_since = customer[
            "customer_since"
        ]

        if isinstance(customer_since, str):
            customer_since = (
                date.fromisoformat(
                    customer_since
                )
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
    def monthly_payment(
        principal: float,
        annual_rate: float,
        term_months: int,
    ) -> float:
        """
        Calculate amortized monthly payment.
        """

        monthly_rate = (
            annual_rate / 12
        )

        if monthly_rate == 0:
            return round(
                principal / term_months,
                2,
            )

        payment = (
            principal
            * monthly_rate
            * (
                1 + monthly_rate
            ) ** term_months
            / (
                (
                    1 + monthly_rate
                ) ** term_months
                - 1
            )
        )

        return round(
            payment,
            2,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def outstanding_balance(
        principal: float,
        status: str,
    ) -> float:
        """
        Generate outstanding loan balance.
        """

        if status == "PAID_OFF":
            return 0.00

        if status == "DEFAULTED":
            percentage = random.uniform(
                0.40,
                0.95,
            )

        elif status == "DELINQUENT":
            percentage = random.uniform(
                0.20,
                0.85,
            )

        else:
            percentage = random.uniform(
                0.05,
                0.95,
            )

        return round(
            principal * percentage,
            2,
        )

    # ------------------------------------------------------------------

    def build_loan(
        self,
        customer: dict,
    ) -> dict | None:
        """
        Build one loan record.
        """

        accounts = self.customer_accounts(
            customer["customer_id"]
        )

        eligible_accounts = [
            account
            for account in accounts
            if account["account_status"]
            != "CLOSED"
        ]

        if not eligible_accounts:
            return None

        account = random.choice(
            eligible_accounts
        )

        loan_type = self.choose_loan_type(
            customer
        )

        principal = self.loan_amount(
            loan_type,
            customer,
        )

        credit_score = int(
            customer.get(
                "credit_score",
                650,
            )
        )

        rate = self.interest_rate(
            loan_type,
            credit_score,
        )

        term = self.loan_term(
            loan_type
        )

        status = self.loan_status()

        originated = self.origination_date(
            customer
        )

        maturity = (
            originated
            + timedelta(
                days=term * 30,
            )
        )

        payment = self.monthly_payment(
            principal,
            rate,
            term,
        )

        balance = self.outstanding_balance(
            principal,
            status,
        )

        created = utc_now()

        return {
            "loan_id":
                generate_id(
                    "LOAN",
                    self.sequence,
                    8,
                ),

            "customer_id":
                customer["customer_id"],

            "account_id":
                account["account_id"],

            "branch_id":
                customer["branch_id"],

            "loan_type":
                loan_type,

            "loan_status":
                status,

            "original_principal":
                principal,

            "outstanding_balance":
                balance,

            "interest_rate":
                rate,

            "term_months":
                term,

            "monthly_payment":
                payment,

            "origination_date":
                originated,

            "maturity_date":
                maturity,

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
        Generate loans.
        """

        self.logger.info(
            "Starting loan generation..."
        )

        loan_count = 0

        skipped_customers = 0

        for customer in self.customers:

            if not self.should_generate_loan(
                customer
            ):
                continue

            loan = self.build_loan(
                customer
            )

            if loan is None:
                skipped_customers += 1
                continue

            self.add(
                loan
            )

            self.sequence += 1

            loan_count += 1

            if loan_count % 10_000 == 0:
                self.logger.info(
                    f"Generated "
                    f"{loan_count:,} loans..."
                )

        self.logger.info(
            f"Customers processed : "
            f"{len(self.customers):,}"
        )

        self.logger.info(
            f"Loans generated : "
            f"{loan_count:,}"
        )

        self.logger.info(
            f"Customers skipped : "
            f"{skipped_customers:,}"
        )

        self.logger.info(
            "Loan generation completed."
        )


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":
    LoanGenerator().run()