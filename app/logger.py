"""Module for logging configuration."""

import logging


class ColoredFormatter(logging.Formatter):
    """
    A custom logging formatter that adds color to log level names based on their severity.

    Attributes:
        COLORS (dict): A dictionary mapping log levels to their corresponding ANSI color codes.
        RESET (str): The ANSI reset code to reset the color formatting.

    Methods:
        format(record):
            Formats the specified log record as text, adding color to the log level name.

            Args:
                record (logging.LogRecord): The log record to be formatted.

            Returns:
                str: The formatted log record with colored log level name.
    """

    COLORS = {
        "DEBUG": "\033[94m",
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m",
        "CRITICAL": "\033[95m",
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a logger with the specified name. The logger is configured to log
    messages at the DEBUG level and outputs to the console with a colored format.

    Args:
        name (str): The name of the logger.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.hasHandlers():
        console_handler = logging.StreamHandler()
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        colored_formatter = ColoredFormatter(log_format)
        console_handler.setFormatter(colored_formatter)
        logger.addHandler(console_handler)

    return logger
