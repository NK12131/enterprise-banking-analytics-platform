"""
Project : Enterprise Banking Analytics Platform
File    : faker_utils.py
Author  : Subashini

Description:
Reusable Faker utility functions used across all data generators.
"""

from __future__ import annotations

from datetime import UTC, datetime

import random

from generators.common.config import RANDOM_SEED

from faker import Faker

from generators.common.config import config

# -----------------------------------------------------------------------------
# Initialize Faker
# -----------------------------------------------------------------------------

fake = Faker("en_US")

Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# -----------------------------------------------------------------------------
# Person
# -----------------------------------------------------------------------------

def first_name() -> str:
    return fake.first_name()


def last_name() -> str:
    return fake.last_name()


def full_name() -> str:
    return fake.name()


def date_of_birth(min_age: int = 18, max_age: int = 85):
    return fake.date_of_birth(
        minimum_age=min_age,
        maximum_age=max_age
    )


# -----------------------------------------------------------------------------
# Contact
# -----------------------------------------------------------------------------

def email(first: str, last: str) -> str:
    domains = [
        "gmail.com",
        "outlook.com",
        "yahoo.com",
        "example.com"
    ]

    return (
        f"{first.lower()}."
        f"{last.lower()}"
        f"{random.randint(100,999)}@"
        f"{random.choice(domains)}"
    )


def phone() -> str:
    return (
        f"+1-"
        f"{random.randint(200,999)}-"
        f"{random.randint(100,999)}-"
        f"{random.randint(1000,9999)}"
    )


# -----------------------------------------------------------------------------
# Address
# -----------------------------------------------------------------------------

def address() -> dict:

    return {
        "street": fake.street_address(),
        "city": fake.city(),
        "state": fake.state(),
        "zip_code": fake.zipcode(),
        "country": "USA"
    }


# -----------------------------------------------------------------------------
# Banking
# -----------------------------------------------------------------------------

def routing_number() -> str:
    return str(random.randint(100000000, 999999999))


def account_number() -> str:
    return str(random.randint(100000000000, 999999999999))


def credit_card_number() -> str:
    return fake.credit_card_number()


# -----------------------------------------------------------------------------
# Company
# -----------------------------------------------------------------------------

def company() -> str:
    return fake.company()


# -----------------------------------------------------------------------------
# Employment
# -----------------------------------------------------------------------------

def job_title() -> str:
    return fake.job()


# -----------------------------------------------------------------------------
# Dates
# -----------------------------------------------------------------------------

def timestamp_between(start_date, end_date):
    if end_date == "today":
        end_date = datetime.now(UTC)

    return fake.date_time_between(
        start_date=start_date,
        end_date=end_date
    )


# -----------------------------------------------------------------------------
# Geographic
# -----------------------------------------------------------------------------

def latitude():

    return round(
        float(fake.latitude()),
        6
    )


def longitude():

    return round(
        float(fake.longitude()),
        6
    )


# -----------------------------------------------------------------------------
# Internet
# -----------------------------------------------------------------------------

def ipv4():

    return fake.ipv4()


def device_id():

    return fake.uuid4()


# -----------------------------------------------------------------------------
# Identifiers
# -----------------------------------------------------------------------------

def uuid():

    return fake.uuid4()