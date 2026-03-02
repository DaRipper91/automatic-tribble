"""
Centralized logging configuration for TFM.
"""
import logging
from rich.logging import RichHandler
from typing import Optional

def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger with RichHandler.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file.

    Returns:
        The configured root logger.
    """
    handlers = [RichHandler(rich_tracebacks=True, markup=True)]

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
        force=True # Force reconfiguration
    )

    logger = logging.getLogger("tfm")
    logger.setLevel(level)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(f"tfm.{name}")
