"""
Project : Enterprise Banking Analytics Platform

File    : customer_profiles.py

Description
-----------
Defines realistic banking customer personas.
"""

from __future__ import annotations

CUSTOMER_PROFILES = {

    "STUDENT": {

        "age": (18, 24),

        "occupations": [
            "Student"
        ],

        "income": (5000, 35000),

        "credit_score": (580, 690),

        "segment": [
            "STANDARD"
        ],

        "account_types": [
            "CHECKING",
            "SAVINGS"
        ],

        "loan_types": [
            "EDUCATION"
        ],

        "credit_card_probability": 0.20,

        "loan_probability": 0.25

    },

    "YOUNG_PROFESSIONAL": {

        "age": (25, 32),

        "occupations": [
            "Software Engineer",
            "Teacher",
            "Financial Analyst",
            "Accountant",
            "Consultant"
        ],

        "income": (60000, 120000),

        "credit_score": (680, 760),

        "net_worth": (50000, 350000),

        "segment": [
            "STANDARD",
            "PREMIUM"
        ],

        "account_types": [
            "CHECKING",
            "SAVINGS"
        ],

        "loan_types": [
            "AUTO",
            "PERSONAL"
        ],

        "credit_card_probability": 0.80,

        "loan_probability": 0.45,

        "preferred_channels": [
            "MOBILE_APP",
            "ONLINE_BANKING"
        ]
    },

    "MID_CAREER": {

        "age": (33, 50),

        "occupations": [

            "Doctor",

            "Lawyer",

            "Architect",

            "Manager",

            "Business Owner"

        ],

        "income": (120000, 300000),

        "credit_score": (720, 820),

        "segment": [

            "PREMIUM",

            "GOLD"

        ],

        "account_types": [

            "CHECKING",

            "SAVINGS"

        ],

        "loan_types": [

            "HOME",

            "AUTO"

        ],

        "credit_card_probability": 0.95,

        "loan_probability": 0.70

    },

    "EXECUTIVE": {

        "age": (40, 65),

        "occupations": [

            "Executive",

            "Business Owner"

        ],

        "income": (300000, 1200000),

        "credit_score": (780, 850),

        "segment": [

            "GOLD",

            "PRIVATE"

        ],

        "account_types": [

            "CHECKING",

            "SAVINGS",

            "BUSINESS"

        ],

        "loan_types": [

            "HOME",

            "BUSINESS"

        ],

        "credit_card_probability": 1.00,

        "loan_probability": 0.85

    },

    "RETIRED": {

        "age": (60, 85),

        "occupations": [

            "Retired"

        ],

        "income": (30000, 150000),

        "credit_score": (700, 820),

        "segment": [

            "STANDARD",

            "PREMIUM"

        ],

        "account_types": [

            "CHECKING",

            "SAVINGS"

        ],

        "loan_types": [

        ],

        "credit_card_probability": 0.50,

        "loan_probability": 0.05

    }

}