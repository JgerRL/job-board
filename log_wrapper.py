# log_wrapper.py
import logging
from logging.handlers import RotatingFileHandler
import os

class LogWrapper:
    def __init__(self, name=__name__, log_file="scraper.log"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Avoid adding duplicate handlers
        if not self.logger.handlers:
            # Create log directory if needed
            os.makedirs("logs", exist_ok=True)
            log_path = os.path.join("logs", log_file)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)

            # File handler (rotates at 5MB, keeps 5 backups)
            file_handler = RotatingFileHandler(
                log_path, maxBytes=5*1024*1024, backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)

            # Add handlers
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
