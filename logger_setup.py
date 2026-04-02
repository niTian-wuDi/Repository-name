import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


class LoggerSetup:
    """日志初始化模块，配置日志记录器"""

    LOG_DIR = "./logs"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @classmethod
    def setup_logger(cls, name: str = "weather_app") -> logging.Logger:
        """
        设置并返回配置好的日志记录器

        Args:
            name: 日志记录器名称

        Returns:
            配置好的日志记录器
        """
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        if logger.handlers:
            return logger

        os.makedirs(cls.LOG_DIR, exist_ok=True)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(cls.LOG_FORMAT, cls.DATE_FORMAT)
        console_handler.setFormatter(console_formatter)

        log_file = os.path.join(cls.LOG_DIR, "weather.log")
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(cls.LOG_FORMAT, cls.DATE_FORMAT)
        file_handler.setFormatter(file_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger
