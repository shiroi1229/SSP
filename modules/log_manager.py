# path: modules/log_manager.py
# version: v2
# 修正版: exc_infoオプションに対応 + 汎用的エラーハンドリング拡張

import logging
from pathlib import Path

class LogManager:
    def __init__(self):
        self.logger = logging.getLogger("ssp_logger")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        fh = logging.FileHandler(log_dir / "feedback_loop.log", encoding="utf-8")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, exc_info=False):
        """exc_info=True を受け取れるよう修正"""
        self.logger.error(message, exc_info=exc_info)

log_manager = LogManager()
