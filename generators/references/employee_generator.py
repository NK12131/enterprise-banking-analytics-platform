"""
Project : Enterprise Banking Analytics Platform

File    : employee_generator.py

Description
-----------
Generates synthetic bank employees for every branch.
"""

from __future__ import annotations

import random
from datetime import timedelta

from generators.common.base_generator import BaseGenerator
from generators.common.constants import BRANCH_STAFFING
from generators.common.data_loader import DataLoader
from generators.common.faker_utils import (
    fake,
)
from generators.common.helpers import (
    generate_id,
    utc_now,
)
from generators.common.validators import validate_employee


class EmployeeGenerator(BaseGenerator):
    """
    Generate bank employee records.
    """

    DATASET_NAME = "employees"

    FILE_PREFIX = "employees"

    VALIDATOR = validate_employee

    RECORD_SOURCE = "SYNTHETIC_GENERATOR"

    def __init__(self) -> None:
        super().__init__()

        self.loader = DataLoader()

        self.branches: list[dict] = (
            self.loader.branches()
        )

        self.sequence = 1

        self.batch_id = utc_now().strftime(
            "%Y%m%d%H%M%S"
        )

    # ------------------------------------------------------------------

    @staticmethod
    def resolve_branch_size(
        branch: dict,
    ) -> str:
        """
        Derive staffing size from branch type.
        """

        branch_type = branch.get(
            "branch_type",
            "RETAIL",
        )

        if branch_type in (
            "HEADQUARTERS",
            "REGIONAL",
        ):
            return "LARGE"

        if branch_type in (
            "COMMERCIAL",
            "BUSINESS",
        ):
            return "MEDIUM"

        return "SMALL"

    # ------------------------------------------------------------------

    @staticmethod
    def employment_status() -> str:
        """
        Generate employee status.
        """

        return random.choices(
            [
                "ACTIVE",
                "LEAVE",
                "TERMINATED",
            ],
            weights=[
                96,
                2,
                2,
            ],
            k=1,
        )[0]

    # ------------------------------------------------------------------

    @staticmethod
    def hire_date():
        """
        Generate employee hire date.
        """

        return fake.date_between(
            start_date="-12y",
            end_date="today",
        )

    # ------------------------------------------------------------------

    @staticmethod
    def termination_date(
        status: str,
        hire_date,
    ):
        """
        Generate termination date when applicable.
        """

        if status != "TERMINATED":
            return None

        earliest_date = (
            hire_date
            + timedelta(days=90)
        )

        today = utc_now().date()

        if earliest_date >= today:
            return None

        return fake.date_between(
            start_date=earliest_date,
            end_date=today,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def annual_salary(
        role: str,
    ) -> float:
        """
        Generate salary based on employee role.
        """

        salary_ranges = {
            "BRANCH_MANAGER": (
                90_000,
                145_000,
            ),
            "ASSISTANT_MANAGER": (
                65_000,
                95_000,
            ),
            "TELLER": (
                35_000,
                52_000,
            ),
            "CUSTOMER_SERVICE_REP": (
                40_000,
                60_000,
            ),
            "PERSONAL_BANKER": (
                50_000,
                80_000,
            ),
            "LOAN_OFFICER": (
                65_000,
                110_000,
            ),
            "RELATIONSHIP_MANAGER": (
                85_000,
                150_000,
            ),
        }

        minimum, maximum = salary_ranges.get(
            role,
            (
                40_000,
                75_000,
            ),
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
    def department(
        role: str,
    ) -> str:
        """
        Derive department from employee role.
        """

        role_department = {
            "BRANCH_MANAGER":
                "BRANCH_MANAGEMENT",

            "ASSISTANT_MANAGER":
                "BRANCH_MANAGEMENT",

            "TELLER":
                "BRANCH_OPERATIONS",

            "CUSTOMER_SERVICE_REP":
                "CUSTOMER_SERVICE",

            "PERSONAL_BANKER":
                "RETAIL_BANKING",

            "LOAN_OFFICER":
                "LENDING",

            "RELATIONSHIP_MANAGER":
                "RELATIONSHIP_BANKING",
        }

        return role_department.get(
            role,
            "BRANCH_OPERATIONS",
        )

    # ------------------------------------------------------------------

    def build_employee(
        self,
        branch: dict,
        role: str,
    ) -> dict:
        """
        Build one employee record.
        """

        status = self.employment_status()

        hire_date = self.hire_date()

        terminated_date = (
            self.termination_date(
                status,
                hire_date,
            )
        )

        if (
            status == "TERMINATED"
            and terminated_date is None
        ):
            status = "ACTIVE"

        created = utc_now()

        first_name = fake.first_name()

        last_name = fake.last_name()

        employee_id = generate_id(
            "EMP",
            self.sequence,
            8,
        )

        return {
            "employee_id":
                employee_id,

            "branch_id":
                branch["branch_id"],

            "branch_code":
                branch["branch_code"],

            "first_name":
                first_name,

            "last_name":
                last_name,

            "email":
                (
                    f"{first_name}.{last_name}."
                    f"{self.sequence}@novabank.com"
                ).lower().replace(
                    " ",
                    "",
                ),

            "phone_number":
                fake.phone_number(),

            "job_title":
                role,

            "department":
                self.department(role),

            "employment_status":
                status,

            "hire_date":
                hire_date,

            "termination_date":
                terminated_date,

            "annual_salary":
                self.annual_salary(role),

            "manager_id":
                None,

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
        Generate employees for all branches.
        """

        self.logger.info(
            "Starting employee generation..."
        )

        employee_count = 0

        for branch in self.branches:

            branch_size = (
                self.resolve_branch_size(
                    branch
                )
            )

            staffing = BRANCH_STAFFING[
                branch_size
            ]

            self.logger.debug(
                "Generating %s branch staffing "
                "for branch %s",
                branch_size,
                branch["branch_id"],
            )

            for role, staffing_range in (
                staffing.items()
            ):

                minimum, maximum = (
                    staffing_range
                )

                role_count = random.randint(
                    minimum,
                    maximum,
                )

                for _ in range(role_count):

                    employee = (
                        self.build_employee(
                            branch=branch,
                            role=role,
                        )
                    )

                    self.add(employee)

                    self.sequence += 1

                    employee_count += 1

        self.logger.info(
            f"Branches processed : "
            f"{len(self.branches):,}"
        )

        self.logger.info(
            f"Employees generated : "
            f"{employee_count:,}"
        )

        self.logger.info(
            "Employee generation completed."
        )


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    EmployeeGenerator().run()