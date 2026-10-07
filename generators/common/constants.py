"""
Project : Enterprise Banking Analytics Platform
File    : constants.py
Author  : Subashini

Description:
Business constants used across all synthetic data generators.
"""

# =============================================================================
# CUSTOMER
# =============================================================================

CUSTOMER_TYPES = [
    "INDIVIDUAL",
    "BUSINESS"
]

CUSTOMER_STATUS = [
    "ACTIVE",
    "INACTIVE",
    "SUSPENDED"
]

GENDERS = [
    "Male",
    "Female",
    "Other"
]

# =============================================================================
# ACCOUNT
# =============================================================================

ACCOUNT_TYPES = [
    "SAVINGS",
    "CHECKING",
    "CURRENT",
    "BUSINESS"
]

ACCOUNT_STATUS = [
    "ACTIVE",
    "CLOSED",
    "FROZEN",
    "DORMANT"
]

# =============================================================================
# CREDIT CARD
# =============================================================================

CARD_TYPES = [
    "VISA",
    "MASTERCARD",
    "AMEX",
    "DISCOVER"
]

CARD_STATUS = [
    "ACTIVE",
    "BLOCKED",
    "EXPIRED"
]

# =============================================================================
# LOANS
# =============================================================================

LOAN_TYPES = [
    "HOME",
    "AUTO",
    "PERSONAL",
    "EDUCATION",
    "BUSINESS"
]

LOAN_STATUS = [
    "ACTIVE",
    "CLOSED",
    "DEFAULT",
    "DELINQUENT"
]

# =============================================================================
# TRANSACTIONS
# =============================================================================

TRANSACTION_TYPES = [
    "ATM_WITHDRAWAL",
    "ATM_DEPOSIT",
    "POS_PURCHASE",
    "ONLINE_PAYMENT",
    "WIRE_TRANSFER",
    "ACH_TRANSFER",
    "SALARY_CREDIT",
    "BILL_PAYMENT",
    "CASH_DEPOSIT",
    "INTEREST_CREDIT"
]

TRANSACTION_STATUS = [
    "SUCCESS",
    "FAILED",
    "PENDING",
    "REVERSED"
]

CHANNELS = [
    "ATM",
    "BRANCH",
    "ONLINE_BANKING",
    "MOBILE_APP",
    "POS",
    "API"
]

# =============================================================================
# MERCHANTS
# =============================================================================

MERCHANT_CATEGORIES = [
    "GROCERY",
    "RESTAURANT",
    "FUEL",
    "TRAVEL",
    "HEALTHCARE",
    "ELECTRONICS",
    "RETAIL",
    "ENTERTAINMENT",
    "EDUCATION",
    "UTILITIES"
]

# =============================================================================
# FRAUD
# =============================================================================

FRAUD_TYPES = [
    "CARD_NOT_PRESENT",
    "ACCOUNT_TAKEOVER",
    "IDENTITY_THEFT",
    "PHISHING",
    "MONEY_LAUNDERING",
    "VELOCITY_ATTACK",
    "SUSPICIOUS_LOCATION",
    "DUPLICATE_TRANSACTION"
]

FRAUD_STATUS = [
    "OPEN",
    "UNDER_REVIEW",
    "CONFIRMED",
    "FALSE_POSITIVE",
    "CLOSED"
]

# =============================================================================
# KYC
# =============================================================================

KYC_STATUS = [
    "VERIFIED",
    "PENDING",
    "REJECTED",
    "EXPIRED"
]

RISK_RATINGS = [
    "LOW",
    "MEDIUM",
    "HIGH"
]

# =============================================================================
# BRANCHES
# =============================================================================

BRANCH_TYPES = [
    "RETAIL",
    "CORPORATE",
    "REGIONAL",
    "HEAD_OFFICE"
]

# =============================================================================
# Branch Staffing Configuration
# =============================================================================

BRANCH_STAFFING = {
    "SMALL": {
        "BRANCH_MANAGER": (1, 1),
        "ASSISTANT_MANAGER": (0, 1),
        "TELLER": (2, 5),
        "CUSTOMER_SERVICE_REP": (1, 3),
        "PERSONAL_BANKER": (1, 2),
        "LOAN_OFFICER": (0, 1),
    },

    "MEDIUM": {
        "BRANCH_MANAGER": (1, 1),
        "ASSISTANT_MANAGER": (1, 2),
        "TELLER": (5, 10),
        "CUSTOMER_SERVICE_REP": (3, 6),
        "PERSONAL_BANKER": (2, 5),
        "LOAN_OFFICER": (1, 3),
    },

    "LARGE": {
        "BRANCH_MANAGER": (1, 1),
        "ASSISTANT_MANAGER": (2, 3),
        "TELLER": (10, 20),
        "CUSTOMER_SERVICE_REP": (5, 10),
        "PERSONAL_BANKER": (5, 10),
        "LOAN_OFFICER": (3, 6),
        "RELATIONSHIP_MANAGER": (2, 5),
    },
}

# =============================================================================
# EMPLOYEES
# =============================================================================

EMPLOYEE_DESIGNATIONS = [
    "Branch Manager",
    "Relationship Manager",
    "Loan Officer",
    "Operations Executive",
    "Cashier",
    "Customer Service Representative",
    "Fraud Analyst",
    "Compliance Officer",
    "Financial Advisor",
    "Regional Manager"
]

# =============================================================================
# CURRENCIES
# =============================================================================

CURRENCIES = [
    "USD",
    "EUR",
    "GBP",
    "CAD",
    "AUD",
    "JPY",
    "INR"
]

# =============================================================================
# US STATES
# =============================================================================

US_STATES = [
    "Texas",
    "California",
    "Florida",
    "New York",
    "Illinois",
    "Georgia",
    "Arizona",
    "Colorado",
    "Washington",
    "North Carolina"
]

# =============================================================================
# BANKING CHANNELS
# =============================================================================

DIGITAL_CHANNELS = [
    "Mobile Banking",
    "Internet Banking",
    "ATM",
    "Branch",
    "Call Center"
]

# =============================================================================
# EVENT TYPES
# =============================================================================

EVENT_TYPES = [
    "LOGIN",
    "LOGOUT",
    "PASSWORD_RESET",
    "NEW_BENEFICIARY",
    "ATM_WITHDRAWAL",
    "ATM_DEPOSIT",
    "CARD_SWIPE",
    "ONLINE_PAYMENT",
    "WIRE_TRANSFER",
    "FAILED_LOGIN"
]
# =============================================================================
# REGION MAPPING
# =============================================================================

REGION_MAPPING = {
    "Texas": "South",
    "Florida": "South",
    "California": "West",
    "Washington": "West",
    "New York": "East",
    "Illinois": "Midwest"
}

# =============================================================================
# TRANSACTION TYPE -> DIRECTION
# =============================================================================

TRANSACTION_DIRECTION = {
    "ATM_WITHDRAWAL": "DEBIT",
    "ATM_DEPOSIT": "CREDIT",
    "POS_PURCHASE": "DEBIT",
    "ONLINE_PAYMENT": "DEBIT",
    "WIRE_TRANSFER": "DEBIT",
    "ACH_TRANSFER": "DEBIT",
    "SALARY_CREDIT": "CREDIT",
    "BILL_PAYMENT": "DEBIT",
    "CASH_DEPOSIT": "CREDIT",
    "INTEREST_CREDIT": "CREDIT"
}

# =============================================================================
# MERCHANT CATEGORY BY TRANSACTION TYPE
# =============================================================================

TRANSACTION_MERCHANT_MAPPING = {

    "ATM_WITHDRAWAL": ["ATM"],

    "ATM_DEPOSIT": ["ATM"],

    "POS_PURCHASE": [
        "GROCERY",
        "RETAIL",
        "FUEL",
        "RESTAURANT",
        "ELECTRONICS"
    ],

    "ONLINE_PAYMENT": [
        "UTILITIES",
        "EDUCATION",
        "HEALTHCARE",
        "RETAIL"
    ],

    "WIRE_TRANSFER": [
        "BANK"
    ],

    "ACH_TRANSFER": [
        "BANK"
    ],

    "SALARY_CREDIT": [
        "EMPLOYER"
    ],

    "BILL_PAYMENT": [
        "UTILITIES"
    ],

    "CASH_DEPOSIT": [
        "BRANCH"
    ],

    "INTEREST_CREDIT": [
        "BANK"
    ]
}