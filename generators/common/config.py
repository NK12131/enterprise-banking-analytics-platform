"""
Configuration Loader

Loads YAML configuration once and exposes project settings.
"""

from __future__ import annotations

from pathlib import Path

import yaml

import os


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = PROJECT_ROOT / "config"

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

ARCHIVE_DIR = DATA_DIR / "archive"

RANDOM_SEED = 42

AWS_REGION = os.getenv(
    "AWS_REGION",
    "us-east-1",
)

S3_RAW_BUCKET = os.getenv(
    "S3_RAW_BUCKET",
    "enterprise-banking-analytics-raw",
)

S3_RAW_PREFIX = os.getenv(
    "S3_RAW_PREFIX",
    "raw",
)

class Config:

    def __init__(self):

        config_file = CONFIG_DIR / "datasets.yml"

        with open(config_file, encoding="utf-8") as file:

            self.settings = yaml.safe_load(file)

    def get(self, key):

        return self.settings[key]


config = Config()