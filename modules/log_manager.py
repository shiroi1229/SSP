import logging
import json
from pathlib import Path
from datetime import datetime

class LogManager:
    def __init__(self, log_dir="devlogs", human_readable_suffix="_human.log", json_suffix="_json.log"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.human_readable_suffix = human_readable_suffix
        self.json_suffix = json_suffix

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Ensure handlers are not duplicated if LogManager is initialized multiple times
        if not self.logger.handlers:
            # Human-readable handler
            human_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            human_handler = logging.FileHandler(self._get_log_filepath(self.human_readable_suffix))
            human_handler.setFormatter(human_formatter)
            self.logger.addHandler(human_handler)

            # JSON handler
            json_formatter = JsonFormatter()
            json_handler = logging.FileHandler(self._get_log_filepath(self.json_suffix))
            json_handler.setFormatter(json_formatter)
            self.logger.addHandler(json_handler)

            # Console handler for immediate feedback
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def _get_log_filepath(self, suffix):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.log_dir / f"ssp_log_{timestamp}{suffix}"

    def info(self, message, extra=None):
        self.logger.info(message, extra=extra)

    def debug(self, message, extra=None):
        self.logger.debug(message, extra=extra)

    def warning(self, message, extra=None):
        self.logger.warning(message, extra=extra)

    def error(self, message, extra=None):
        self.logger.error(message, extra=extra)

    def exception(self, message, extra=None):
        self.logger.exception(message, extra=extra)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "levelname": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            log_record["stack_info"] = self.formatStack(record.stack_info)
        if hasattr(record, 'extra_data'):
            log_record.update(record.extra_data)
        return json.dumps(log_record, ensure_ascii=False)

# Global instance for easy access across modules
log_manager = LogManager()
