"""同步 cron 文件。"""

from __future__ import annotations

import logging
import os
import sys

from rainyun.data.store import DataStore
from rainyun.scheduler.cron import write_cron_file

logger = logging.getLogger(__name__)

_LOG_FILE_PATH = os.environ.get("LOG_FILE", "data/logs/rainyun.log")


def ensure_file_handler() -> None:
    root = logging.getLogger()
    for handler in root.handlers:
        if isinstance(handler, logging.FileHandler) and getattr(handler, "baseFilename", ""):
            if os.path.abspath(handler.baseFilename) == os.path.abspath(_LOG_FILE_PATH):
                return
    try:
        os.makedirs(os.path.dirname(_LOG_FILE_PATH), exist_ok=True)
    except Exception:
        return
    handler = logging.FileHandler(_LOG_FILE_PATH, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    root.addHandler(handler)


def main() -> int:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    ensure_file_handler()
    try:
        store = DataStore()
        data = store.load()
        normalized = write_cron_file(data.settings.cron_schedule)
        logger.info("cron 计划已同步: %s", normalized)
        return 0
    except Exception as exc:
        logger.exception("cron 同步失败: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
