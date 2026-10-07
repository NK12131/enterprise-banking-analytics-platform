"""
Project : Enterprise Banking Analytics Platform
File    : validators.py

Description
-----------
Business validation utilities used by all generators.
"""

from __future__ import annotations

import re
from typing import Any


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


class ValidationError(Exception):
    """Raised when a generated record fails validation."""


# =============================================================================
# Generic Validators
# =============================================================================

def require(value: Any, field_name: str) -> None:
    """Ensure a required field is present."""

    if value is None:
        raise ValidationError(f"{field_name} cannot be None")

    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")


def positive_number(value: float | int, field_name: str) -> None:
    """Ensure numeric value is positive."""

    if value < 0:
        raise ValidationError(
            f"{field_name} cannot be negative"
        )


def valid_email(email: str) -> None:
    """Validate email format."""

    require(email, "email")

    if not EMAIL_PATTERN.match(email):
        raise ValidationError(
            f"Invalid email: {email}"
        )


def one_of(
    value: str,
    allowed: list[str],
    field_name: str,
) -> None:

    if value not in allowed:
        raise ValidationError(
            f"{field_name} must be one of {allowed}"
        )


# =============================================================================
# Customer
# =============================================================================

def validate_customer(record: dict) -> None:

    require(record["customer_id"], "customer_id")
    require(record["first_name"], "first_name")
    require(record["last_name"], "last_name")

    valid_email(record["email"])

    positive_number(
        record["annual_income"],
        "annual_income",
    )


# =============================================================================
# Account
# =============================================================================

def validate_account(
    record: dict,
) -> bool:
    """
    Validate account record.
    """

    required_fields = (
        "account_id",
        "account_number",
        "customer_id",
        "branch_id",
        "branch_code",
        "account_type",
        "account_status",
        "currency_code",
        "current_balance",
        "available_balance",
        "interest_rate",
        "opened_date",
        "created_timestamp",
        "updated_timestamp",
        "batch_id",
        "record_source",
    )

    # ------------------------------------------------------------------
    # Required fields
    # ------------------------------------------------------------------

    for field in required_fields:

        if field not in record:
            return False

        if record[field] is None:
            return False

    # ------------------------------------------------------------------
    # Account ID
    # ------------------------------------------------------------------

    account_id = record["account_id"]

    if not isinstance(
        account_id,
        str,
    ):
        return False

    if not account_id.startswith("ACC"):
        return False

    # ------------------------------------------------------------------
    # Account number
    # ------------------------------------------------------------------

    account_number = record[
        "account_number"
    ]

    if not isinstance(
        account_number,
        str,
    ):
        return False

    if not account_number.isdigit():
        return False

    # ------------------------------------------------------------------
    # Account type
    # ------------------------------------------------------------------

    valid_account_types = {
        "CHECKING",
        "SAVINGS",
        "MONEY_MARKET",
    }

    if (
        record["account_type"]
        not in valid_account_types
    ):
        return False

    # ------------------------------------------------------------------
    # Account status
    # ------------------------------------------------------------------

    valid_account_statuses = {
        "ACTIVE",
        "DORMANT",
        "CLOSED",
    }

    account_status = record[
        "account_status"
    ]

    if (
        account_status
        not in valid_account_statuses
    ):
        return False

    # ------------------------------------------------------------------
    # Currency
    # ------------------------------------------------------------------

    if record["currency_code"] != "USD":
        return False

    # ------------------------------------------------------------------
    # Balances
    # ------------------------------------------------------------------

    current_balance = record[
        "current_balance"
    ]

    available_balance = record[
        "available_balance"
    ]

    if not isinstance(
        current_balance,
        (int, float),
    ):
        return False

    if not isinstance(
        available_balance,
        (int, float),
    ):
        return False

    if current_balance < 0:
        return False

    if available_balance < 0:
        return False

    if (
        available_balance
        > current_balance
    ):
        return False

    # ------------------------------------------------------------------
    # Interest rate
    # ------------------------------------------------------------------

    interest_rate = record[
        "interest_rate"
    ]

    if not isinstance(
        interest_rate,
        (int, float),
    ):
        return False

    if interest_rate < 0:
        return False

    # ------------------------------------------------------------------
    # Closure consistency
    # ------------------------------------------------------------------

    closed_date = record.get(
        "closed_date"
    )

    if (
        account_status == "CLOSED"
        and closed_date is None
    ):
        return False

    if (
        account_status != "CLOSED"
        and closed_date is not None
    ):
        return False

    if (
        account_status == "CLOSED"
        and current_balance != 0
    ):
        return False

    if (
        account_status == "CLOSED"
        and available_balance != 0
    ):
        return False

    return True


# =============================================================================
# Transaction
# =============================================================================

def validate_transaction(
    record: dict,
) -> bool:
    """
    Validate transaction record against the final
    TransactionGenerator schema.
    """

    required_fields = (
        "transaction_id",
        "account_id",
        "customer_id",
        "branch_id",
        "transaction_type",
        "transaction_direction",
        "transaction_amount",
        "transaction_status",
        "transaction_timestamp",
        "transaction_channel",
        "currency_code",
        "created_timestamp",
        "updated_timestamp",
        "batch_id",
        "record_source",
    )

    # ------------------------------------------------------------------
    # Required fields
    # ------------------------------------------------------------------

    for field in required_fields:

        if field not in record:
            return False

        if record[field] is None:
            return False

    # ------------------------------------------------------------------
    # Transaction ID
    # ------------------------------------------------------------------

    transaction_id = record[
        "transaction_id"
    ]

    if not isinstance(
        transaction_id,
        str,
    ):
        return False

    if not transaction_id.startswith(
        "TXN"
    ):
        return False

    # ------------------------------------------------------------------
    # Transaction type
    # ------------------------------------------------------------------

    valid_transaction_types = {
        "PURCHASE",
        "ATM_WITHDRAWAL",
        "DEPOSIT",
        "TRANSFER_IN",
        "TRANSFER_OUT",
        "BILL_PAYMENT",
    }

    transaction_type = record[
        "transaction_type"
    ]

    if (
        transaction_type
        not in valid_transaction_types
    ):
        return False

    # ------------------------------------------------------------------
    # Transaction direction
    # ------------------------------------------------------------------

    valid_directions = {
        "DEBIT",
        "CREDIT",
    }

    transaction_direction = record[
        "transaction_direction"
    ]

    if (
        transaction_direction
        not in valid_directions
    ):
        return False

    credit_types = {
        "DEPOSIT",
        "TRANSFER_IN",
    }

    expected_direction = (
        "CREDIT"
        if transaction_type in credit_types
        else "DEBIT"
    )

    if (
        transaction_direction
        != expected_direction
    ):
        return False

    # ------------------------------------------------------------------
    # Transaction amount
    # ------------------------------------------------------------------

    transaction_amount = record[
        "transaction_amount"
    ]

    if not isinstance(
        transaction_amount,
        (int, float),
    ):
        return False

    if transaction_amount <= 0:
        return False

    # ------------------------------------------------------------------
    # Transaction status
    # ------------------------------------------------------------------

    valid_transaction_statuses = {
        "COMPLETED",
        "PENDING",
        "DECLINED",
        "REVERSED",
    }

    if (
        record["transaction_status"]
        not in valid_transaction_statuses
    ):
        return False

    # ------------------------------------------------------------------
    # Transaction channel
    # ------------------------------------------------------------------

    valid_channels = {
        "MOBILE",
        "ONLINE",
        "ATM",
        "BRANCH",
        "POS",
    }

    transaction_channel = record[
        "transaction_channel"
    ]

    if (
        transaction_channel
        not in valid_channels
    ):
        return False

    # ------------------------------------------------------------------
    # Channel consistency
    # ------------------------------------------------------------------

    if (
        transaction_type
        == "ATM_WITHDRAWAL"
        and transaction_channel != "ATM"
    ):
        return False

    if (
        transaction_type == "PURCHASE"
        and transaction_channel != "POS"
    ):
        return False

    # ------------------------------------------------------------------
    # Merchant consistency
    # ------------------------------------------------------------------

    merchant_name = record.get(
        "merchant_name"
    )

    merchant_category = record.get(
        "merchant_category"
    )

    if transaction_type == "PURCHASE":

        if merchant_name is None:
            return False

        if merchant_category is None:
            return False

    else:

        if merchant_name is not None:
            return False

        if merchant_category is not None:
            return False

    # ------------------------------------------------------------------
    # Location consistency
    # ------------------------------------------------------------------

    transaction_city = record.get(
        "transaction_city"
    )

    transaction_state = record.get(
        "transaction_state"
    )

    if transaction_channel in {
        "MOBILE",
        "ONLINE",
    }:

        if transaction_city is not None:
            return False

        if transaction_state is not None:
            return False

    # ------------------------------------------------------------------
    # Currency
    # ------------------------------------------------------------------

    if record["currency_code"] != "USD":
        return False

    return True


# =============================================================================
# Loan
# =============================================================================

def validate_loan(
    record: dict,
) -> bool:
    """
    Validate loan record against the final
    LoanGenerator schema.
    """

    required_fields = (
        "loan_id",
        "customer_id",
        "account_id",
        "branch_id",
        "loan_type",
        "loan_status",
        "original_principal",
        "outstanding_balance",
        "interest_rate",
        "term_months",
        "monthly_payment",
        "origination_date",
        "maturity_date",
        "currency_code",
        "created_timestamp",
        "updated_timestamp",
        "batch_id",
        "record_source",
    )

    # ------------------------------------------------------------------
    # Required fields
    # ------------------------------------------------------------------

    for field in required_fields:

        if field not in record:
            return False

        if record[field] is None:
            return False

    # ------------------------------------------------------------------
    # Loan ID
    # ------------------------------------------------------------------

    loan_id = record["loan_id"]

    if not isinstance(
        loan_id,
        str,
    ):
        return False

    if not loan_id.startswith("LOAN"):
        return False

    # ------------------------------------------------------------------
    # Loan type
    # ------------------------------------------------------------------

    valid_loan_types = {
        "PERSONAL_LOAN",
        "AUTO_LOAN",
        "MORTGAGE",
        "HOME_EQUITY",
    }

    if (
        record["loan_type"]
        not in valid_loan_types
    ):
        return False

    # ------------------------------------------------------------------
    # Loan status
    # ------------------------------------------------------------------

    valid_loan_statuses = {
        "ACTIVE",
        "PAID_OFF",
        "DELINQUENT",
        "DEFAULTED",
    }

    loan_status = record[
        "loan_status"
    ]

    if (
        loan_status
        not in valid_loan_statuses
    ):
        return False

    # ------------------------------------------------------------------
    # Principal
    # ------------------------------------------------------------------

    original_principal = record[
        "original_principal"
    ]

    if not isinstance(
        original_principal,
        (int, float),
    ):
        return False

    if original_principal <= 0:
        return False

    # ------------------------------------------------------------------
    # Outstanding balance
    # ------------------------------------------------------------------

    outstanding_balance = record[
        "outstanding_balance"
    ]

    if not isinstance(
        outstanding_balance,
        (int, float),
    ):
        return False

    if outstanding_balance < 0:
        return False

    if (
        outstanding_balance
        > original_principal
    ):
        return False

    # ------------------------------------------------------------------
    # Paid-off consistency
    # ------------------------------------------------------------------

    if (
        loan_status == "PAID_OFF"
        and outstanding_balance != 0
    ):
        return False

    # ------------------------------------------------------------------
    # Interest rate
    # ------------------------------------------------------------------

    interest_rate = record[
        "interest_rate"
    ]

    if not isinstance(
        interest_rate,
        (int, float),
    ):
        return False

    if not (
        0 <= interest_rate <= 1
    ):
        return False

    # ------------------------------------------------------------------
    # Loan term
    # ------------------------------------------------------------------

    term_months = record[
        "term_months"
    ]

    if not isinstance(
        term_months,
        int,
    ):
        return False

    if term_months <= 0:
        return False

    # ------------------------------------------------------------------
    # Monthly payment
    # ------------------------------------------------------------------

    monthly_payment = record[
        "monthly_payment"
    ]

    if not isinstance(
        monthly_payment,
        (int, float),
    ):
        return False

    if monthly_payment <= 0:
        return False

    # ------------------------------------------------------------------
    # Currency
    # ------------------------------------------------------------------

    if (
        record["currency_code"]
        != "USD"
    ):
        return False

    # ------------------------------------------------------------------
    # Date consistency
    # ------------------------------------------------------------------

    origination_date = record[
        "origination_date"
    ]

    maturity_date = record[
        "maturity_date"
    ]

    if (
        maturity_date
        <= origination_date
    ):
        return False

    return True


# =============================================================================
# Credit Card
# =============================================================================

def validate_credit_card(record: dict) -> None:

    require(record["card_id"], "card_id")

    positive_number(
        record["credit_limit"],
        "credit_limit",
    )

    positive_number(
        record["available_credit"],
        "available_credit",
    )


# =============================================================================
# Fraud
# =============================================================================

def validate_fraud(record: dict) -> None:

    require(
        record["fraud_id"],
        "fraud_id",
    )

    require(
        record["transaction_id"],
        "transaction_id",
    )

    positive_number(
        record["risk_score"],
        "risk_score",
    )

def validate_employee(
    record: dict,
) -> bool:
    """
    Validate employee record.
    """

    required_fields = (
        "employee_id",
        "branch_id",
        "branch_code",
        "first_name",
        "last_name",
        "job_title",
        "department",
        "employment_status",
        "hire_date",
        "annual_salary",
        "batch_id",
        "record_source",
    )

    # --------------------------------------------------------------
    # Required fields
    # --------------------------------------------------------------

    for field in required_fields:
        if field not in record:
            return False

        if record[field] is None:
            return False

    # --------------------------------------------------------------
    # Employee ID
    # --------------------------------------------------------------

    employee_id = record["employee_id"]

    if not isinstance(employee_id, str):
        return False

    if not employee_id.startswith("EMP"):
        return False

    # --------------------------------------------------------------
    # Employment status
    # --------------------------------------------------------------

    valid_statuses = {
        "ACTIVE",
        "LEAVE",
        "TERMINATED",
    }

    if (
        record["employment_status"]
        not in valid_statuses
    ):
        return False

    # --------------------------------------------------------------
    # Salary
    # --------------------------------------------------------------

    salary = record["annual_salary"]

    if not isinstance(
        salary,
        (int, float),
    ):
        return False

    if salary <= 0:
        return False

    # --------------------------------------------------------------
    # Termination consistency
    # --------------------------------------------------------------

    status = record[
        "employment_status"
    ]

    termination_date = record.get(
        "termination_date"
    )

    if (
        status == "TERMINATED"
        and termination_date is None
    ):
        return False

    if (
        status != "TERMINATED"
        and termination_date is not None
    ):
        return False

    return True