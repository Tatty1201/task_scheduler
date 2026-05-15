"""logging 設定ユーティリティ。"""
from __future__ import annotations

import logging
import os
import sys


def setup_logger(name: str = "task_scheduler") -> logging.Logger:
    """環境変数 LOG_LEVEL に従ったロガーを返す。

    複数回呼ばれてもハンドラを重複登録しない。
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.propagate = False

    return logger
