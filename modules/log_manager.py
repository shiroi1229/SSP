# path: modules/log_manager.py
# version: v2
# 修正版: exc_infoオプションに対応 + 汎用的エラーハンドリング拡張

import logging
from pathlib import Path
import json # Added json import for JsonFormatter
from datetime import datetime # Added datetime import for _get_log_filepath
import sys # Added import for sys.stdout

class LogManager:
    def __init__(self):
        self.logger = logging.getLogger("ssp_logger")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers to prevent duplicates during hot-reloads
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler for feedback_loop.log
        fh = logging.FileHandler(log_dir / "feedback_loop.log", encoding="utf-8")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Console handler
        ch = logging.StreamHandler(sys.stdout, encoding="utf-8") # Added sys.stdout and encoding
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # JSON handler (re-added for consistency with previous versions)
        json_formatter = JsonFormatter()
        json_handler = logging.FileHandler(self._get_log_filepath("_json.log"))
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)

    def _get_log_filepath(self, suffix):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return Path("logs") / f"ssp_log_{timestamp}{suffix}"

    def info(self, message, extra=None):
        self.logger.info(message, extra=extra)

    def debug(self, message, extra=None):
        self.logger.debug(message, extra=extra)

    def warning(self, message, extra=None):
        self.logger.warning(message, extra=extra)

    def error(self, message, exc_info=False, extra=None):
        """exc_info=True を受け取れるよう修正"""
        self.logger.error(message, exc_info=exc_info, extra=extra)

    def exception(self, message, extra=None):
        """Logs a message with exception information. Automatically sets exc_info=True."""
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