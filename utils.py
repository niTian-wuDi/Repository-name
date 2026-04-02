import os
from datetime import datetime
from typing import Any, Dict

from logger_setup import LoggerSetup


class WeatherFormatter:
    """天气数据格式化工具"""

    @staticmethod
    def format_console(data: Dict[str, Any]) -> str:
        """
        格式化天气数据为控制台输出格式

        Args:
            data: 天气数据字典

        Returns:
            格式化后的字符串
        """
        lines = [
            "=" * 50,
            "[天气] 实时天气信息",
            "=" * 50,
            f"城市: {data.get('city', '未知')}",
            f"温度: {data.get('temperature', 'N/A')}C",
            f"湿度: {data.get('humidity', 'N/A')}%",
            f"天气: {data.get('condition', '未知')}",
            f"风向: {data.get('wind_direction', '未知')}",
            f"风速: {data.get('wind_speed', 'N/A')} km/h",
            f"更新时间: {data.get('update_time', '未知')}",
            "=" * 50,
        ]
        return "\n".join(lines)

    @staticmethod
    def format_file(data: Dict[str, Any]) -> str:
        """
        格式化天气数据为文件存储格式

        Args:
            data: 天气数据字典

        Returns:
            格式化后的字符串
        """
        lines = [
            f"记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"城市: {data.get('city', '未知')}",
            f"温度: {data.get('temperature', 'N/A')}°C",
            f"湿度: {data.get('humidity', 'N/A')}%",
            f"天气状况: {data.get('condition', '未知')}",
            f"风向: {data.get('wind_direction', '未知')}",
            f"风速: {data.get('wind_speed', 'N/A')} km/h",
            f"API更新时间: {data.get('update_time', '未知')}",
            "-" * 40,
            "",
        ]
        return "\n".join(lines)


class FileManager:
    """文件管理工具"""

    OUTPUT_DIR = "./output"

    def __init__(self):
        self._logger = LoggerSetup.setup_logger(__name__)

    def save_weather_data(self, data: Dict[str, Any], filename: str = None) -> str:
        """
        保存天气数据到文件

        Args:
            data: 天气数据字典
            filename: 文件名，默认为日期命名

        Returns:
            保存的文件路径
        """
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

        if filename is None:
            filename = f"weather_{datetime.now().strftime('%Y%m%d')}.txt"

        filepath = os.path.join(self.OUTPUT_DIR, filename)

        formatter = WeatherFormatter()
        content = formatter.format_file(data)

        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(content)
            self._logger.info(f"天气数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            self._logger.error(f"保存天气数据失败: {e}")
            raise

    def ensure_directory(self, path: str) -> bool:
        """
        确保目录存在

        Args:
            path: 目录路径

        Returns:
            是否成功
        """
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            self._logger.error(f"创建目录失败 {path}: {e}")
            return False


class TimeUtils:
    """时间工具类"""

    @staticmethod
    def get_current_time() -> str:
        """获取当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_current_date() -> str:
        """获取当前日期字符串"""
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        格式化日期时间

        Args:
            dt: datetime对象
            fmt: 格式字符串

        Returns:
            格式化后的字符串
        """
        return dt.strftime(fmt)

    @staticmethod
    def parse_interval_to_seconds(value: int, unit: str) -> int:
        """
        将间隔时间转换为秒数

        Args:
            value: 间隔数值
            unit: 间隔单位 (minutes/hours)

        Returns:
            秒数
        """
        if unit == "minutes":
            return value * 60
        elif unit == "hours":
            return value * 3600
        else:
            return value * 60


class StringUtils:
    """字符串工具类"""

    @staticmethod
    def safe_string(value: Any, max_length: int = 100) -> str:
        """
        安全转换字符串

        Args:
            value: 任意值
            max_length: 最大长度

        Returns:
            字符串
        """
        if value is None:
            return ""
        s = str(value)
        if len(s) > max_length:
            s = s[:max_length] + "..."
        return s

    @staticmethod
    def is_empty(s: str) -> bool:
        """检查字符串是否为空或仅包含空白"""
        return s is None or len(s.strip()) == 0
