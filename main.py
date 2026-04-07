import signal
import sys
import threading
import time
from typing import Optional

from config import ConfigLoader
from logger_setup import LoggerSetup
from utils import FileManager, TimeUtils, WeatherFormatter
from validator import ConfigValidator, ValidationError
from weather_fetcher import WeatherService


class WeatherScheduler:
    """天气定时任务调度器"""

    def __init__(self):
        self._logger = LoggerSetup.setup_logger(__name__)
        self._config_loader = ConfigLoader()
        self._config_validator = ConfigValidator()
        self._file_manager = FileManager()
        self._weather_service: Optional[WeatherService] = None
        self._running = False
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """启动定时任务"""
        self._logger.info("=" * 60)
        self._logger.info("天气小程序启动")
        self._logger.info("=" * 60)

        try:
            config = self._config_loader.load()
            is_valid, errors = self._config_validator.validate(config)
            if not is_valid:
                error_msg = "; ".join(errors)
                self._logger.error(f"配置校验失败: {error_msg}")
                raise ValidationError(f"配置错误: {error_msg}")

            self._weather_service = WeatherService(
                api_key=self._config_loader.api_key
            )

            self._running = True
            self._logger.info(f"目标城市: {self._config_loader.city}")
            self._logger.info(
                f"定时间隔: {self._config_loader.interval_value} "
                f"{self._config_loader.interval_unit}"
            )

            self._execute_task()

        except Exception as e:
            self._logger.error(f"启动失败: {e}")
            raise

    def stop(self) -> None:
        """停止定时任务"""
        self._logger.info("正在停止定时任务...")
        with self._lock:
            self._running = False
            if self._timer:
                self._timer.cancel()
                self._timer = None
        self._logger.info("定时任务已停止")

    def _execute_task(self) -> None:
        """执行天气获取任务"""
        if not self._running:
            return

        try:
            self._fetch_and_save_weather()
        except Exception as e:
            self._logger.error(f"任务执行失败: {e}")

        self._schedule_next()

    def _fetch_and_save_weather(self) -> None:
        """获取并保存天气数据"""
        city = self._config_loader.city

        try:
            weather_data = self._weather_service.get_weather(city)

            formatter = WeatherFormatter()
            console_output = formatter.format_console(weather_data)
            print("\n" + console_output)

            if self._config_loader.output_enabled:
                self._file_manager.save_weather_data(weather_data)

        except Exception as e:
            self._logger.error(f"获取天气数据失败: {e}")
            print(f"\n[错误] 获取天气数据失败: {e}")
            raise

    def _schedule_next(self) -> None:
        """调度下一次任务"""
        with self._lock:
            if not self._running:
                return

            interval_seconds = TimeUtils.parse_interval_to_seconds(
                self._config_loader.interval_value,
                self._config_loader.interval_unit
            )

            self._logger.debug(f"下一次任务将在 {interval_seconds} 秒后执行")

            self._timer = threading.Timer(interval_seconds, self._execute_task)
            self._timer.daemon = True
            self._timer.start()

    def run_once(self) -> None:
        """仅执行一次任务（用于测试）"""
        try:
            config = self._config_loader.load()
            is_valid, errors = self._config_validator.validate(config)
            if not is_valid:
                error_msg = "; ".join(errors)
                raise ValidationError(f"配置错误: {error_msg}")

            self._weather_service = WeatherService(
                api_key=self._config_loader.api_key
            )
            self._fetch_and_save_weather()

        except Exception as e:
            self._logger.error(f"执行失败: {e}")
            raise


def signal_handler(signum, frame):
    """信号处理函数"""
    logger = LoggerSetup.setup_logger("signal_handler")
    logger.info(f"接收到信号 {signum}，正在退出...")
    if scheduler:
        scheduler.stop()
    sys.exit(0)


scheduler: Optional[WeatherScheduler] = None


def main():
    """程序入口"""
    global scheduler

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    scheduler = WeatherScheduler()

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            scheduler.run_once()
        else:
            scheduler.start()
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"\n程序异常: {e}")
        sys.exit(1)
    finally:
        if scheduler:
            scheduler.stop()


if __name__ == "__main__":
    main()
