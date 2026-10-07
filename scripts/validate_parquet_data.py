"""
Project : Enterprise Banking Analytics Platform

File    : validate_parquet_data.py

Description
-----------
Scalable Parquet data-quality validation using PyArrow.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pyarrow.dataset as ds
import pyarrow.compute as pc

from generators.common.config import RAW_DATA_DIR


class ParquetDataValidator:
    """
    Validate generated Parquet datasets.
    """

    DATASETS = {
        "branches": "branch_id",
        "employees": "employee_id",
        "customers": "customer_id",
        "accounts": "account_id",
        "loans": "loan_id",
        "credit_cards": "card_id",
        "transactions": "transaction_id",
        "fraud": "fraud_case_id",
    }

    def __init__(self) -> None:
        self.raw_data_dir = Path(
            RAW_DATA_DIR
        )

        self.failures: list[str] = []

    # ------------------------------------------------------------------

    def dataset_path(
        self,
        dataset_name: str,
    ) -> Path:
        """
        Resolve dataset directory.
        """

        return (
            self.raw_data_dir
            / dataset_name
        )

    # ------------------------------------------------------------------

    def load_dataset(
        self,
        dataset_name: str,
    ) -> ds.Dataset | None:
        """
        Load Parquet dataset.
        """

        path = self.dataset_path(
            dataset_name
        )

        files = list(
            path.glob("*.parquet")
        )

        if not files:
            self.failures.append(
                f"{dataset_name}: "
                "no Parquet files found"
            )

            print(
                f"[FAIL] {dataset_name:<20} "
                "no Parquet files"
            )

            return None

        return ds.dataset(
            path,
            format="parquet",
        )

    # ------------------------------------------------------------------

    def validate_row_count(
        self,
        dataset_name: str,
        dataset: ds.Dataset,
    ) -> None:
        """
        Validate dataset row count.
        """

        row_count = dataset.count_rows()

        if row_count <= 0:
            self.failures.append(
                f"{dataset_name}: empty dataset"
            )

            print(
                f"[FAIL] {dataset_name:<20} EMPTY"
            )

            return

        print(
            f"[PASS] {dataset_name:<20} "
            f"{row_count:>12,} rows"
        )

    # ------------------------------------------------------------------

    def validate_primary_key(
        self,
        dataset_name: str,
        dataset: ds.Dataset,
        primary_key: str,
    ) -> None:
        """
        Validate primary-key nulls and uniqueness.
        """

        table = dataset.to_table(
            columns=[
                primary_key,
            ]
        )

        column = table[
            primary_key
        ]

        null_count = column.null_count

        if null_count:
            self.failures.append(
                f"{dataset_name}.{primary_key}: "
                f"{null_count:,} null values"
            )

            print(
                f"[FAIL] "
                f"{dataset_name}.{primary_key} "
                f"{null_count:,} nulls"
            )

            return

        distinct_count = len(
            pc.unique(column)
        )

        row_count = len(column)

        duplicate_count = (
            row_count - distinct_count
        )

        if duplicate_count:
            self.failures.append(
                f"{dataset_name}.{primary_key}: "
                f"{duplicate_count:,} duplicates"
            )

            print(
                f"[FAIL] "
                f"{dataset_name}.{primary_key} "
                f"{duplicate_count:,} duplicates"
            )

            return

        print(
            f"[PASS] "
            f"{dataset_name}.{primary_key} "
            "unique"
        )

    # ------------------------------------------------------------------

    def validate_schema(
        self,
        dataset_name: str,
        dataset: ds.Dataset,
        required_fields: set[str],
    ) -> None:
        """
        Validate required schema fields.
        """

        schema_fields = set(
            dataset.schema.names
        )

        missing_fields = (
            required_fields
            - schema_fields
        )

        if missing_fields:
            self.failures.append(
                f"{dataset_name}: missing fields "
                f"{sorted(missing_fields)}"
            )

            print(
                f"[FAIL] {dataset_name:<20} "
                f"missing fields: "
                f"{sorted(missing_fields)}"
            )

            return

        print(
            f"[PASS] {dataset_name:<20} "
            "schema valid"
        )

    # ------------------------------------------------------------------

    def validate_business_rules(
        self,
    ) -> None:
        """
        Validate major business rules.
        """

        print("\nBUSINESS RULE VALIDATION")
        print("=" * 80)

        self.validate_account_rules()

        self.validate_loan_rules()

        self.validate_card_rules()

        self.validate_transaction_rules()

        self.validate_fraud_rules()

    # ------------------------------------------------------------------

    def validate_account_rules(
        self,
    ) -> None:

        dataset = self.load_dataset(
            "accounts"
        )

        if dataset is None:
            return

        table = dataset.to_table(
            columns=[
                "account_status",
                "current_balance",
            ]
        )

        invalid = pc.and_(
            pc.equal(
                table["account_status"],
                "CLOSED",
            ),
            pc.not_equal(
                table["current_balance"],
                0,
            ),
        )

        count = pc.sum(
            pc.cast(
                invalid,
                "int64",
            )
        ).as_py()

        self.report_rule(
            "Closed accounts have zero balance",
            count,
        )

    # ------------------------------------------------------------------

    def validate_loan_rules(
        self,
    ) -> None:

        dataset = self.load_dataset(
            "loans"
        )

        if dataset is None:
            return

        table = dataset.to_table(
            columns=[
                "loan_status",
                "outstanding_balance",
            ]
        )

        invalid = pc.and_(
            pc.equal(
                table["loan_status"],
                "PAID_OFF",
            ),
            pc.not_equal(
                table["outstanding_balance"],
                0,
            ),
        )

        count = pc.sum(
            pc.cast(
                invalid,
                "int64",
            )
        ).as_py()

        self.report_rule(
            "Paid-off loans have zero balance",
            count,
        )

    # ------------------------------------------------------------------

    def validate_card_rules(
        self,
    ) -> None:

        dataset = self.load_dataset(
            "credit_cards"
        )

        if dataset is None:
            return

        table = dataset.to_table(
            columns=[
                "credit_limit",
                "available_credit",
            ]
        )

        invalid = pc.or_(
            pc.less(
                table["available_credit"],
                0,
            ),
            pc.greater(
                table["available_credit"],
                table["credit_limit"],
            ),
        )

        count = pc.sum(
            pc.cast(
                invalid,
                "int64",
            )
        ).as_py()

        self.report_rule(
            "Available credit is valid",
            count,
        )

    # ------------------------------------------------------------------

    def validate_transaction_rules(
        self,
    ) -> None:

        dataset = self.load_dataset(
            "transactions"
        )

        if dataset is None:
            return

        scanner = dataset.scanner(
            columns=[
                "transaction_amount",
            ],
            batch_size=100_000,
        )

        invalid_count = 0

        for batch in scanner.to_batches():

            invalid = pc.less_equal(
                batch["transaction_amount"],
                0,
            )

            count = pc.sum(
                pc.cast(
                    invalid,
                    "int64",
                )
            ).as_py()

            invalid_count += count or 0

        self.report_rule(
            "Transaction amounts are positive",
            invalid_count,
        )

    # ------------------------------------------------------------------

    def validate_fraud_rules(
        self,
    ) -> None:

        dataset = self.load_dataset(
            "fraud"
        )

        if dataset is None:
            return

        table = dataset.to_table(
            columns=[
                "risk_score",
            ]
        )

        invalid = pc.or_(
            pc.less(
                table["risk_score"],
                0,
            ),
            pc.greater(
                table["risk_score"],
                100,
            ),
        )

        count = pc.sum(
            pc.cast(
                invalid,
                "int64",
            )
        ).as_py()

        self.report_rule(
            "Fraud risk scores are valid",
            count,
        )

    # ------------------------------------------------------------------

    def report_rule(
        self,
        rule_name: str,
        violation_count: int,
    ) -> None:

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
        Execute Parquet audit.
        """

        print()
        print("=" * 80)
        print(
            "ENTERPRISE BANKING PARQUET DATA AUDIT"
        )
        print("=" * 80)

        required_schemas = {
            "branches": {
                "branch_id",
                "branch_code",
            },
            "employees": {
                "employee_id",
                "branch_id",
            },
            "customers": {
                "customer_id",
                "branch_id",
                "profile",
            },
            "accounts": {
                "account_id",
                "customer_id",
                "current_balance",
            },
            "loans": {
                "loan_id",
                "customer_id",
                "original_principal",
            },
            "credit_cards": {
                "card_id",
                "customer_id",
                "credit_limit",
            },
            "transactions": {
                "transaction_id",
                "account_id",
                "transaction_amount",
            },
            "fraud": {
                "fraud_case_id",
                "transaction_id",
                "risk_score",
            },
        }

        print("\nDATASET VALIDATION")
        print("=" * 80)

        for (
            dataset_name,
            primary_key,
        ) in self.DATASETS.items():

            dataset = self.load_dataset(
                dataset_name
            )

            if dataset is None:
                continue

            self.validate_row_count(
                dataset_name,
                dataset,
            )

            self.validate_schema(
                dataset_name,
                dataset,
                required_schemas[
                    dataset_name
                ],
            )

            self.validate_primary_key(
                dataset_name,
                dataset,
                primary_key,
            )

        self.validate_business_rules()

        print("\nAUDIT SUMMARY")
        print("=" * 80)

        if not self.failures:

            print(
                "[PASS] All Parquet data "
                "quality checks passed."
            )

            return True

        print(
            f"[FAIL] {len(self.failures):,} "
            "checks failed."
        )

        for failure in self.failures:

            print(
                f"  - {failure}"
            )

        return False


if __name__ == "__main__":

    validator = ParquetDataValidator()

    success = validator.run()

    sys.exit(
        0 if success else 1
    )