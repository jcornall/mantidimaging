# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Module for commonly used functions across the modules.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QSettings

from mantidimaging.core.data import ImageStack


def initialise_logging(arg_level: str) -> None:
    log_formatter = logging.Formatter("%(asctime)s [%(name)s:L%(lineno)d] %(levelname)s: %(message)s")

    settings = QSettings()
    setting_level = settings.value("logging/log_level", defaultValue="INFO")

    if arg_level:
        log_level = logging.getLevelName(arg_level)
    else:
        log_level = logging.getLevelName(setting_level)

    # Capture all warnings
    logging.captureWarnings(True)

    # Remove default handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Stdout handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # File handler
    log_directory = Path(settings.value("logging/log_dir", defaultValue=""))
    if log_directory != Path(""):
        filename = f"mantid_imaging_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        if not log_directory.exists():
            log_directory.mkdir()
        file_log = logging.FileHandler(log_directory / filename)
        file_log.setFormatter(log_formatter)
        root_logger.addHandler(file_log)

    # Default log level for mantidimaging only
    logging.getLogger('mantidimaging').setLevel(log_level)

    perf_logger = logging.getLogger('perf')
    perf_logger.setLevel(100)
    perf_logger.propagate = False
    if settings.value("logging/performance_log", defaultValue=False, type=bool):
        perf_logger.setLevel(1)
        perf_logger.addHandler(console_handler)
        if log_directory != Path(""):
            perf_logger.addHandler(file_log)


def check_data_stack(data, expected_dims=3, expected_class=ImageStack):
    """
    Make sure the data has expected dimensions and class.
    """
    if data is None:
        raise ValueError("Data is a None type.")

    if not isinstance(data, expected_class):
        raise ValueError(
            f"Invalid data type. It must be an {expected_class.__name__} object. Instead found: {type(data).__name__}")

    if expected_dims != data.data.ndim:
        raise ValueError(f"Invalid data format. It does not have 3 dimensions. Shape: {data.data.shape}")
