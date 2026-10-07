"""
Project : Enterprise Banking Analytics Platform

File    : customer_generator.py

Description
-----------
Generates synthetic retail banking customer records.

Architecture
------------
- Uses list[dict]
- Loads branches through DataLoader
- Uses customer personas
- Writes through BaseGenerator
- Preserves branch referential integrity
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from generators.common.base_generator import BaseGenerator
from generators.common.customer_profiles import CUSTOMER_PROFILES
from generators.common.data_loader import DataLoader
from generators.common.faker_utils import fake
from generators.common.helpers import generate_id, utc_now
from generators.common.validators import validate_customer


# =============================================================================
# Configuration
# =============================================================================

CUSTOMER_COUNT = 100_000

CUSTOMER_STATUS = [
    "ACTIVE",
    "INACTIVE",
    "CLOSED",
]

CUSTOMER_STATUS_WEIGHTS = [
    96,
    3,
    1,
]

GENDERS = [
    "MALE",
    "FEMALE",
]

GENDER_WEIGHTS = [
    49,
    51,
]

MARITAL_STATUS = [
    "SINGLE",
    "MARRIED",
    "DIVORCED",
    "WIDOWED",
]

MARITAL_STATUS_WEIGHTS = [
    35,
    50,
    10,
    5,
]


# =============================================================================
# Customer Generator
# =============================================================================


class CustomerGenerator(BaseGenerator):
    """
    Generate synthetic banking customers.
    """

    DATASET_NAME = "customers"

    FILE_PREFIX = "customers"

    VALIDATOR = validate_customer

    RECORD_SOURCE = "SYNTHETIC_GENERATOR"

    # ------------------------------------------------------------------

    def __init__(self) -> None:
        super().__init__()

        self.loader = DataLoader()

        self.branches: list[dict] = (
            self.loader.branches()
        )

        if not self.branches:
            raise RuntimeError(
                "No branch records found. "
                "Run branch_generator before customer_generator."
            )

        self.sequence = 1

        self.batch_id = utc_now().strftime(
            "%Y%m%d%H%M%S"
        )

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------

    @staticmethod
    def choose_profile() -> str:
        """
        Select a customer persona.
        """

        profiles = list(
            CUSTOMER_PROFILES.keys()
        )

        weights = [
            CUSTOMER_PROFILES[profile].get(
                "weight",
                1,
            )
            for profile in profiles
        ]

        return random.choices(
            population=profiles,
            weights=weights,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def profile_age_range(
        profile: dict,
    ) -> tuple[int, int]:
        """
        Resolve age range from customer profile.
        """

        age_range = profile.get(
            "age_range",
            (18, 80),
        )

        return (
            int(age_range[0]),
            int(age_range[1]),
        )

    # ------------------------------------------------------------------
    # Demographics
    # ------------------------------------------------------------------

    @staticmethod
    def gender() -> str:
        """
        Generate gender.
        """

        return random.choices(
            population=GENDERS,
            weights=GENDER_WEIGHTS,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def marital_status() -> str:
        """
        Generate marital status.
        """

        return random.choices(
            population=MARITAL_STATUS,
            weights=MARITAL_STATUS_WEIGHTS,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def date_of_birth(
        minimum_age: int,
        maximum_age: int,
    ) -> date:
        """
        Generate date of birth from age range.
        """

        today = utc_now().date()

        age = random.randint(
            minimum_age,
            maximum_age,
        )

        approximate_birth_date = (
            today
            - timedelta(
                days=age * 365,
            )
        )

        return approximate_birth_date - timedelta(
            days=random.randint(
                0,
                364,
            )
        )

    # ------------------------------------------------------------------

    @staticmethod
    def calculate_age(
        date_of_birth: date,
    ) -> int:
        """
        Calculate customer age.
        """

        today = utc_now().date()

        return (
            today.year
            - date_of_birth.year
            - (
                (
                    today.month,
                    today.day,
                )
                <
                (
                    date_of_birth.month,
                    date_of_birth.day,
                )
            )
        )

    # ------------------------------------------------------------------
    # Financial profile
    # ------------------------------------------------------------------

    @staticmethod
    def annual_income(
        profile: dict,
    ) -> float:
        """
        Generate annual income from profile.
        """

        income_range = profile.get(
            "income_range",
            (
                25_000,
                150_000,
            ),
        )

        minimum, maximum = income_range

        return round(
            random.uniform(
                minimum,
                maximum,
            ),
            2,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def credit_score(
        profile: dict,
    ) -> int:
        """
        Generate customer credit score.
        """

        score_range = profile.get(
            "credit_score_range",
            (
                580,
                850,
            ),
        )

        minimum, maximum = score_range

        return random.randint(
            int(minimum),
            int(maximum),
        )

    # ------------------------------------------------------------------

    @staticmethod
    def customer_segment(
        profile_name: str,
        profile: dict,
    ) -> str:
        """
        Resolve customer segment.
        """

        return profile.get(
            "segment",
            profile_name,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def risk_rating(
        credit_score: int,
    ) -> str:
        """
        Derive customer risk rating.
        """

        if credit_score >= 760:
            return "LOW"

        if credit_score >= 680:
            return "MEDIUM"

        if credit_score >= 600:
            return "HIGH"

        return "CRITICAL"

    # ------------------------------------------------------------------
    # Customer lifecycle
    # ------------------------------------------------------------------

    @staticmethod
    def customer_status() -> str:
        """
        Generate customer status.
        """

        return random.choices(
            population=CUSTOMER_STATUS,
            weights=CUSTOMER_STATUS_WEIGHTS,
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def customer_since() -> date:
        """
        Generate customer relationship start date.
        """

        return fake.date_between(
            start_date="-15y",
            end_date="-30d",
        )

    # ------------------------------------------------------------------

    @staticmethod
    def closed_date(
        status: str,
        customer_since: date,
    ) -> date | None:
        """
        Generate customer closure date.
        """

        if status != "CLOSED":
            return None

        earliest_date = (
            customer_since
            + timedelta(days=30)
        )

        today = utc_now().date()

        if earliest_date >= today:
            return today

        return fake.date_between(
            start_date=earliest_date,
            end_date=today,
        )

    # ------------------------------------------------------------------
    # Contact
    # ------------------------------------------------------------------

    @staticmethod
    def email_address(
        first_name: str,
        last_name: str,
        sequence: int,
    ) -> str:
        """
        Generate deterministic unique customer email.
        """

        first = (
            first_name
            .lower()
            .replace(" ", "")
            .replace("'", "")
        )

        last = (
            last_name
            .lower()
            .replace(" ", "")
            .replace("'", "")
        )

        return (
            f"{first}.{last}.{sequence}"
            "@example.com"
        )

    # ------------------------------------------------------------------
    # Record construction
    # ------------------------------------------------------------------

    def build_customer(
        self,
        sequence: int,
    ) -> dict:
        """
        Build one customer record.
        """

        profile_name = self.choose_profile()

        profile = CUSTOMER_PROFILES[
            profile_name
        ]

        branch = random.choice(
            self.branches
        )

        minimum_age, maximum_age = (
            self.profile_age_range(
                profile
            )
        )

        dob = self.date_of_birth(
            minimum_age,
            maximum_age,
        )

        age = self.calculate_age(dob)

        income = self.annual_income(
            profile
        )

        score = self.credit_score(
            profile
        )

        segment = self.customer_segment(
            profile_name,
            profile,
        )

        risk = self.risk_rating(
            score
        )

        status = self.customer_status()

        relationship_start = (
            self.customer_since()
        )

        relationship_closed = (
            self.closed_date(
                status,
                relationship_start,
            )
        )

        first_name = fake.first_name()

        last_name = fake.last_name()

        created = utc_now()

        customer_id = generate_id(
            "CUST",
            sequence,
            8,
        )

        return {
            # ------------------------------------------------------
            # Keys
            # ------------------------------------------------------

            "customer_id":
                customer_id,

            "branch_id":
                branch["branch_id"],

            "branch_code":
                branch["branch_code"],

            # ------------------------------------------------------
            # Profile
            # ------------------------------------------------------

            "profile":
                profile_name,

            "customer_segment":
                segment,

            # ------------------------------------------------------
            # Identity
            # ------------------------------------------------------

            "first_name":
                first_name,

            "last_name":
                last_name,

            "gender":
                self.gender(),

            "date_of_birth":
                dob,

            "age":
                age,

            "marital_status":
                self.marital_status(),

            # ------------------------------------------------------
            # Contact
            # ------------------------------------------------------

            "email":
                self.email_address(
                    first_name,
                    last_name,
                    sequence,
                ),

            "phone_number":
                fake.phone_number(),

            # ------------------------------------------------------
            # Address
            # ------------------------------------------------------

            "address_line_1":
                fake.street_address(),

            "city":
                branch.get(
                    "city",
                    fake.city(),
                ),

            "state":
                branch.get(
                    "state",
                    fake.state_abbr(),
                ),

            "postal_code":
                fake.postcode(),

            "country":
                "USA",

            # ------------------------------------------------------
            # Financial profile
            # ------------------------------------------------------

            "annual_income":
                income,

            "credit_score":
                score,

            "risk_rating":
                risk,

            # ------------------------------------------------------
            # Lifecycle
            # ------------------------------------------------------

            "customer_status":
                status,

            "customer_since":
                relationship_start,

            "closed_date":
                relationship_closed,

            # ------------------------------------------------------
            # Audit
            # ------------------------------------------------------

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
    # Generation
    # ------------------------------------------------------------------

    def generate(self) -> None:
        """
        Generate customer records.
        """

        self.logger.info(
            f"Generating "
            f"{CUSTOMER_COUNT:,} customers..."
        )

        for sequence in range(
            1,
            CUSTOMER_COUNT + 1,
        ):

            customer = self.build_customer(
                sequence
            )

            self.add(
                customer
            )

            self.sequence = (
                sequence + 1
            )

            if sequence % 10_000 == 0:

                self.logger.info(
                    f"Generated "
                    f"{sequence:,} customers..."
                )

        self.logger.info(
            f"Customers generated : "
            f"{CUSTOMER_COUNT:,}"
        )

        self.logger.info(
            "Customer generation completed."
        )


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":
    CustomerGenerator().run()

