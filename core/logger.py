"""Zentrales Logging-Setup für die gesamte Pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logger(log_level: str = "INFO", log_datei: str = "pipeline.log") -> None:
    """
    Konfiguriert den Root-Logger mit Konsolen- und Datei-Handler.

    Args:
        log_level: DEBUG | INFO | WARNING | ERROR
        log_datei: Pfad zur Logdatei
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)
    # Doppelte Handler vermeiden (z.B. bei mehrfachem Aufruf)
    root.handlers.clear()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    log_pfad = Path(log_datei).resolve()
    file_handler = logging.FileHandler(str(log_pfad), encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

