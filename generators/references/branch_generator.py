"""
Project : Enterprise Banking Analytics Platform

File    : branch_generator.py

Description
-----------
Generates bank branch master data.
"""

from __future__ import annotations

import random

from generators.common.base_generator import BaseGenerator
from generators.common.config import config
from generators.common.constants import BRANCH_TYPES
from generators.common.faker_utils import (
    address,
    latitude,
    longitude,
    phone,
)
from generators.common.helpers import (
    generate_id,
    utc_now,
)

# =============================================================================
# Regions
# =============================================================================

STATE_REGION = {
    "Texas": "South",
    "Florida": "South",
    "Georgia": "South",
    "California": "West",
    "Washington": "West",
    "Arizona": "West",
    "Colorado": "Mountain",
    "Illinois": "Midwest",
    "Ohio": "Midwest",
    "New York": "East",
    "New Jersey": "East",
    "Massachusetts": "East",
}

# =============================================================================


class BranchGenerator(BaseGenerator):

    DATASET_NAME = "branches"

    FILE_PREFIX = "branches"

    PARTITIONED = False

    # ------------------------------------------------------------------

    def build_branch(
        self,
        sequence: int,
    ) -> dict:

        addr = address()

        state = addr["state"]

        timestamp = utc_now()

        return {

            "branch_id":
                generate_id(
                    "BR",
                    sequence,
                    5
                ),

            "branch_code":
                f"BR{1000 + sequence}",

            "branch_name":
                f"{addr['city']} Branch",

            "branch_type":
                random.choice(
                    BRANCH_TYPES
                ),
            "branch_size": random.choices(
                ["SMALL", "MEDIUM", "LARGE"],
                weights=[45,35,20],
                k=1
            )[0],

            "street_address":
                addr["street"],

            "city":
                addr["city"],

            "state":
                state,

            "postal_code":
                addr["zip_code"],

            "country":
                "USA",

            "region":
                STATE_REGION.get(
                    state,
                    "Central"
                ),

            "latitude":
                latitude(),

            "longitude":
                longitude(),

            "phone_number":
                phone(),

            "email":
                (
                    f"branch{sequence}"
                    "@novabank.com"
                ),

            "is_active":
                random.choices(
                    [True, False],
                    weights=[98, 2],
                    k=1
                )[0],

            "created_timestamp":
                timestamp,

            "updated_timestamp":
                timestamp

        }

    # ------------------------------------------------------------------

    def generate(self):

        total = config.get(
            "branches"
        )["records"]

        self.logger.info(
            "Generating %s branches...",
            total
        )

        for sequence in range(
            1,
            total + 1
        ):

            branch = self.build_branch(
                sequence
            )

            self.add(branch)


# =============================================================================

if __name__ == "__main__":

    BranchGenerator().run()