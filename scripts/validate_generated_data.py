"""
Project : Enterprise Banking Analytics Platform

File    : validate_generated_data.py

Description
-----------
Performs cross-dataset data quality validation
for generated banking datasets.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable

from generators.common.data_loader import DataLoader


class DataQualityValidator:
    """
    Validate generated banking datasets.
    """

    def __init__(self) -> None:
        self.loader = DataLoader()

        self.branches = self.loader.branches()
        self.customers = self.loader.customers()
        self.accounts = self.loader.accounts()
        self.loans = self.loader.loans()
        self.credit_cards = self.loader.credit_cards()
        self.transactions = self.loader.transactions()
        self.fraud = self.loader.fraud()

        self.failures: list[str] = []

    # ------------------------------------------------------------------

    @staticmethod
    def values(
        records: Iterable[dict],
        field: str,
    ) -> set:
        """
        Return unique non-null values for a field.
        """

        return {
            record[field]
            for record in records
            if record.get(field) is not None
        }

    # ------------------------------------------------------------------

    def check_not_empty(
        self,
        dataset_name: str,
        records: list[dict],
    ) -> None:
        """
        Validate dataset contains records.
        """

        if records:
            print(
                f"[PASS] {dataset_name:<20} "
                f"{len(records):>12,} records"
            )
            return

        self.failures.append(
            f"{dataset_name} is empty"
        )

        print(
            f"[FAIL] {dataset_name:<20} EMPTY"
        )

    # ------------------------------------------------------------------

    def check_unique(
        self,
        dataset_name: str,
        records: list[dict],
        field: str,
    ) -> None:
        """
        Validate primary-key uniqueness.
        """

        values = [
            record.get(field)
            for record in records
        ]

        duplicate_count = (
            len(values) - len(set(values))
        )

        if duplicate_count == 0:
            print(
                f"[PASS] {dataset_name}.{field:<30} "
                "unique"
            )
            return

        self.failures.append(
            f"{dataset_name}.{field} has "
            f"{duplicate_count:,} duplicates"
        )

        print(
            f"[FAIL] {dataset_name}.{field:<30} "
            f"{duplicate_count:,} duplicates"
        )

    # ------------------------------------------------------------------

    def check_required_fields(
        self,
        dataset_name: str,
        records: list[dict],
        fields: tuple[str, ...],
    ) -> None:
        """
        Validate required fields are non-null.
        """

        for field in fields:

            null_count = sum(
                1
                for record in records
                if record.get(field) is None
            )

            if null_count == 0:
                print(
                    f"[PASS] "
                    f"{dataset_name}.{field:<30} "
                    "no nulls"
                )
                continue

            self.failures.append(
                f"{dataset_name}.{field} has "
                f"{null_count:,} null values"
            )

            print(
                f"[FAIL] "
                f"{dataset_name}.{field:<30} "
                f"{null_count:,} nulls"
            )

    # ------------------------------------------------------------------

    def check_foreign_key(
        self,
        child_name: str,
        child_records: list[dict],
        child_field: str,
        parent_name: str,
        parent_records: list[dict],
        parent_field: str,
    ) -> None:
        """
        Validate referential integrity.
        """

        parent_values = self.values(
            parent_records,
            parent_field,
        )

        orphan_values = {
            record.get(child_field)
            for record in child_records
            if (
                record.get(child_field)
                is not None
                and record.get(child_field)
                not in parent_values
            )
        }

        if not orphan_values:
            print(
                f"[PASS] {child_name}.{child_field} "
                f"-> {parent_name}.{parent_field}"
            )
            return

        self.failures.append(
            f"{child_name}.{child_field} has "
            f"{len(orphan_values):,} orphan keys"
        )

        print(
            f"[FAIL] {child_name}.{child_field} "
            f"-> {parent_name}.{parent_field}: "
            f"{len(orphan_values):,} orphan keys"
        )

    # ------------------------------------------------------------------

    def validate_counts(self) -> None:
        """
        Validate datasets are populated.
        """

        print("\nDATASET COUNTS")
        print("=" * 80)

        datasets = {
            "branches": self.branches,
            "customers": self.customers,
            "accounts": self.accounts,
            "loans": self.loans,
            "credit_cards": self.credit_cards,
            "transactions": self.transactions,
            "fraud": self.fraud,
        }

        for name, records in datasets.items():
            self.check_not_empty(
                name,
                records,
            )

    # ------------------------------------------------------------------

    def validate_primary_keys(self) -> None:
        """
        Validate primary-key uniqueness.
        """

        print("\nPRIMARY KEY VALIDATION")
        print("=" * 80)

        checks = (
            (
                "branches",
                self.branches,
                "branch_id",
            ),
            (
                "customers",
                self.customers,
                "customer_id",
            ),
            (
                "accounts",
                self.accounts,
                "account_id",
            ),
            (
                "loans",
                self.loans,
                "loan_id",
            ),
            (
                "credit_cards",
                self.credit_cards,
                "card_id",
            ),
            (
                "transactions",
                self.transactions,
                "transaction_id",
            ),
            (
                "fraud",
                self.fraud,
                "fraud_case_id",
            ),
        )

        for (
            dataset_name,
            records,
            field,
        ) in checks:

            self.check_unique(
                dataset_name,
                records,
                field,
            )

    # ------------------------------------------------------------------

    def validate_required_fields(self) -> None:
        """
        Validate critical fields.
        """

        print("\nREQUIRED FIELD VALIDATION")
        print("=" * 80)

        self.check_required_fields(
            "customers",
            self.customers,
            (
                "customer_id",
                "branch_id",
                "profile",
                "customer_status",
            ),
        )

        self.check_required_fields(
            "accounts",
            self.accounts,
            (
                "account_id",
                "customer_id",
                "branch_id",
                "account_type",
                "account_status",
            ),
        )

        self.check_required_fields(
            "loans",
            self.loans,
            (
                "loan_id",
                "customer_id",
                "account_id",
                "loan_type",
                "loan_status",
            ),
        )

        self.check_required_fields(
            "credit_cards",
            self.credit_cards,
            (
                "card_id",
                "customer_id",
                "account_id",
                "card_product",
                "card_status",
            ),
        )

        self.check_required_fields(
            "transactions",
            self.transactions,
            (
                "transaction_id",
                "account_id",
                "customer_id",
                "transaction_type",
                "transaction_amount",
            ),
        )

        self.check_required_fields(
            "fraud",
            self.fraud,
            (
                "fraud_case_id",
                "transaction_id",
                "account_id",
                "customer_id",
                "risk_score",
                "risk_level",
            ),
        )

    # ------------------------------------------------------------------

    def validate_referential_integrity(
        self,
    ) -> None:
        """
        Validate cross-dataset relationships.
        """

        print("\nREFERENTIAL INTEGRITY")
        print("=" * 80)

        self.check_foreign_key(
            "customers",
            self.customers,
            "branch_id",
            "branches",
            self.branches,
            "branch_id",
        )

        self.check_foreign_key(
            "accounts",
            self.accounts,
            "customer_id",
            "customers",
            self.customers,
            "customer_id",
        )

        self.check_foreign_key(
            "accounts",
            self.accounts,
            "branch_id",
            "branches",
            self.branches,
            "branch_id",
        )

        self.check_foreign_key(
            "loans",
            self.loans,
            "customer_id",
            "customers",
            self.customers,
            "customer_id",
        )

        self.check_foreign_key(
            "loans",
            self.loans,
            "account_id",
            "accounts",
            self.accounts,
            "account_id",
        )

        self.check_foreign_key(
            "credit_cards",
            self.credit_cards,
            "customer_id",
            "customers",
            self.customers,
            "customer_id",
        )

        self.check_foreign_key(
            "credit_cards",
            self.credit_cards,
            "account_id",
            "accounts",
            self.accounts,
            "account_id",
        )

        self.check_foreign_key(
            "transactions",
            self.transactions,
            "account_id",
            "accounts",
            self.accounts,
            "account_id",
        )

        self.check_foreign_key(
            "transactions",
            self.transactions,
            "customer_id",
            "customers",
            self.customers,
            "customer_id",
        )

        self.check_foreign_key(
            "fraud",
            self.fraud,
            "transaction_id",
            "transactions",
            self.transactions,
            "transaction_id",
        )

    # ------------------------------------------------------------------

    def validate_business_rules(self) -> None:
        """
        Validate banking business rules.
        """

        print("\nBUSINESS RULE VALIDATION")
        print("=" * 80)

        invalid_closed_accounts = sum(
            1
            for account in self.accounts
            if (
                account["account_status"] == "CLOSED"
                and account["current_balance"] != 0
            )
        )

        self.report_rule(
            "Closed accounts have zero balance",
            invalid_closed_accounts,
        )

        invalid_paid_loans = sum(
            1
            for loan in self.loans
            if (
                loan["loan_status"] == "PAID_OFF"
                and loan["outstanding_balance"] != 0
            )
        )

        self.report_rule(
            "Paid-off loans have zero balance",
            invalid_paid_loans,
        )

        invalid_card_credit = sum(
            1
            for card in self.credit_cards
            if (
                card["available_credit"] < 0
                or card["available_credit"]
                > card["credit_limit"]
            )
        )

        self.report_rule(
            "Card available credit is valid",
            invalid_card_credit,
        )

        invalid_fraud_scores = sum(
            1
            for fraud in self.fraud
            if not (
                0
                <= fraud["risk_score"]
                <= 100
            )
        )

        self.report_rule(
            "Fraud scores are between 0 and 100",
            invalid_fraud_scores,
        )

    # ------------------------------------------------------------------

    def report_rule(
        self,
        rule_name: str,
        violation_count: int,
    ) -> None:
        """
        Report business-rule result.
        """

        if violation_count == 0:
            print(
                f"[PASS] {rule_name}"
            )
            return

        self.failures.append(
            f"{rule_name}: "
            f"{violation_count:,} violations"
        )

        print(
            f"[FAIL] {rule_name}: "
            f"{violation_count:,} violations"
        )

    # ------------------------------------------------------------------

    def run(self) -> bool:
        """
        Execute complete validation suite.
        """

        print("\n")
        print("=" * 80)
        print(
            "ENTERPRISE BANKING DATA QUALITY AUDIT"
        )
        print("=" * 80)

        self.validate_counts()

        self.validate_primary_keys()

        self.validate_required_fields()

        self.validate_referential_integrity()

        self.validate_business_rules()

        print("\nAUDIT SUMMARY")
        print("=" * 80)

        if not self.failures:

            print(
                "[PASS] All data quality checks passed."
            )

            return True

        print(
            f"[FAIL] {len(self.failures):,} "
            "data quality checks failed."
        )

        for failure in self.failures:
            print(
                f"  - {failure}"
            )

        return False


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":

    validator = DataQualityValidator()

    success = validator.run()

    sys.exit(
        0 if success else 1
    )