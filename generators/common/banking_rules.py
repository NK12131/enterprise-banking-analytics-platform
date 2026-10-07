"""
Project : Enterprise Banking Analytics Platform

File    : banking_rules.py

Description
-----------
Reusable banking business rules shared across generators.
"""

from __future__ import annotations

import math
import random


# =============================================================================
# Risk
# =============================================================================

def determine_risk_rating(credit_score: int) -> str:
    """
    Derive customer risk from credit score.
    """

    if credit_score >= 760:
        return "LOW"

    if credit_score >= 680:
        return "MEDIUM"

    return "HIGH"


# =============================================================================
# Loan Approval
# =============================================================================

def loan_approval_probability(
    credit_score: int,
) -> float:

    if credit_score >= 780:
        return 0.98

    if credit_score >= 720:
        return 0.90

    if credit_score >= 680:
        return 0.75

    if credit_score >= 620:
        return 0.50

    return 0.20


def is_loan_approved(
    credit_score: int,
) -> bool:

    probability = loan_approval_probability(
        credit_score
    )

    return random.random() <= probability


# =============================================================================
# Interest Rates
# =============================================================================

def loan_interest_rate(
    credit_score: int,
) -> float:

    if credit_score >= 780:
        return 4.50

    if credit_score >= 720:
        return 5.50

    if credit_score >= 680:
        return 6.75

    if credit_score >= 620:
        return 8.25

    return 11.00


# =============================================================================
# Credit Card Limit
# =============================================================================

def credit_limit(
    annual_income: float,
    customer_segment: str,
) -> float:

    multiplier = {
        "STANDARD": 0.20,
        "PREMIUM": 0.35,
        "GOLD": 0.50,
        "PRIVATE": 0.75,
    }

    limit = annual_income * multiplier[
        customer_segment
    ]

    return round(limit, -2)


# =============================================================================
# Debt-To-Income
# =============================================================================

def debt_to_income_ratio(
    monthly_income: float,
    monthly_debt: float,
) -> float:

    if monthly_income <= 0:
        return 0.0

    return round(
        monthly_debt / monthly_income,
        2,
    )


# =============================================================================
# EMI
# =============================================================================

def monthly_payment(
    principal: float,
    annual_rate: float,
    years: int,
) -> float:
    """
    Standard loan EMI calculation.
    """

    months = years * 12

    monthly_rate = annual_rate / 100 / 12

    if monthly_rate == 0:

        return round(
            principal / months,
            2,
        )

    emi = (
        principal
        * monthly_rate
        * math.pow(
            1 + monthly_rate,
            months,
        )
    ) / (
        math.pow(
            1 + monthly_rate,
            months,
        )
        - 1
    )

    return round(
        emi,
        2,
    )


# =============================================================================
# Outstanding Balance
# =============================================================================

def outstanding_balance(
    principal: float,
) -> float:
    """
    Simulate remaining loan balance.
    """

    paid_percent = random.uniform(
        0.05,
        0.85,
    )

    return round(
        principal * (1 - paid_percent),
        2,
    )


# =============================================================================
# Account Balance
# =============================================================================

def opening_balance(
    customer_segment: str,
):

    ranges = {

        "STANDARD": (500, 8000),

        "PREMIUM": (8000, 35000),

        "GOLD": (35000, 150000),

        "PRIVATE": (150000, 2000000),

    }

    minimum, maximum = ranges[
        customer_segment
    ]

    return round(
        random.uniform(
            minimum,
            maximum,
        ),
        2,
    )