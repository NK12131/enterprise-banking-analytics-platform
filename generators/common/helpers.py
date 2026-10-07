"""
Project : Enterprise Banking Analytics Platform
File    : helpers.py

Description
-----------
Common helper functions used across all generators.
"""

from __future__ import annotations

import json
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

# =============================================================================
# DATETIME
# =============================================================================

DATE_FORMAT = "%Y-%m-%d"


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def random_datetime(
    start_date: str,
    end_date: str,
) -> datetime:
    """
    Generate a random datetime between two dates.

    Parameters
    ----------
    start_date : str
        Example: "2025-01-01"

    end_date : str
        Example: "2026-12-31"
    """

    start = datetime.strptime(
        start_date,
        DATE_FORMAT
    ).replace(tzinfo=UTC)

    end = datetime.strptime(
        end_date,
        DATE_FORMAT
    ).replace(tzinfo=UTC)

    delta_seconds = int(
        (end - start).total_seconds()
    )

    return start + timedelta(
        seconds=random.randint(0, delta_seconds)
    )


# =============================================================================
# IDS
# =============================================================================

def generate_id(
    prefix: str,
    number: int,
    width: int = 8,
) -> str:

    return f"{prefix}{number:0{width}d}"


def generate_uuid() -> str:

    return str(uuid.uuid4())


# =============================================================================
# MONEY
# =============================================================================

def random_amount(
    minimum: float,
    maximum: float,
    decimals: int = 2,
) -> float:

    return round(
        random.uniform(minimum, maximum),
        decimals
    )


# =============================================================================
# RANDOM
# =============================================================================

def chance(
    probability: float
) -> bool:
    """
    chance(0.20)

    -> 20%
    """

    return random.random() <= probability


def choose(values):

    return random.choice(values)


# =============================================================================
# PARTITION
# =============================================================================

def partition_directory(
    base_directory: Path,
    load_datetime: datetime,
) -> Path:

    folder = (
        base_directory /
        f"load_date={load_datetime.strftime('%Y-%m-%d')}"
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return folder


# =============================================================================
# DATAFRAME
# =============================================================================

def to_dataframe(
    records: list[dict[str, Any]]
) -> pd.DataFrame:

    return pd.DataFrame(records)


# =============================================================================
# WRITE JSON
# =============================================================================

def write_json(
    records: list,
    output_file: Path,
):

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=4,
            default=str
        )


# =============================================================================
# WRITE PARQUET
# =============================================================================

def write_parquet(
    df: pd.DataFrame,
    output_file: Path,
):

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_parquet(
        output_file,
        index=False,
        engine="pyarrow"
    )


# =============================================================================
# WRITE CSV
# =============================================================================

def write_csv(
    df: pd.DataFrame,
    output_file: Path,
):

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        output_file,
        index=False
    )


# =============================================================================
# LOAD JSON
# =============================================================================

def load_json_directory(
    directory: Path,
) -> list:

    records = []

    files = sorted(
        directory.rglob("*.json")
    )

    for file in files:

        with open(
            file,
            encoding="utf-8"
        ) as f:

            records.extend(
                json.load(f)
            )

    return records


# =============================================================================
# LOAD PARQUET
# =============================================================================

def load_parquet_directory(
    directory: Path,
) -> pd.DataFrame:

    files = sorted(
        directory.rglob("*.parquet")
    )

    if not files:

        return pd.DataFrame()

    dfs = [
        pd.read_parquet(file)
        for file in files
    ]

    return pd.concat(
        dfs,
        ignore_index=True
    )


# =============================================================================
# LOAD CSV
# =============================================================================

def load_csv(
    file_path: Path,
) -> pd.DataFrame:

    return pd.read_csv(file_path)


# =============================================================================
# FILE COUNT
# =============================================================================

def file_count(
    directory: Path
) -> int:

    return len(
        [
            f
            for f in directory.rglob("*")
            if f.is_file()
        ]
    )


# =============================================================================
# RECORD COUNT
# =============================================================================

def record_count(
    df: pd.DataFrame
) -> int:

    return len(df)


# =============================================================================
# PROGRESS
# =============================================================================

def print_banner(
    message: str
):

    print()

    print("=" * 80)

    print(message)

    print("=" * 80)