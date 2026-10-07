"""
Central Logging
"""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path

import yaml

from generators.common.config import CONFIG_DIR


config_file = CONFIG_DIR / "logging.yml"

Path("logs").mkdir(exist_ok=True)

with open(config_file, encoding="utf-8") as file:

    logging.config.dictConfig(
        yaml.safe_load(file)
    )


def get_logger(name):

    return logging.getLogger(name)