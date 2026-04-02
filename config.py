import os
from typing import Any, Dict, Optional

import yaml

from logger_setup import LoggerSetup


class ConfigLoader:
    """配置加载器，负责读取和解析YAML配置文件"""

    CONFIG_PATH = "./config/settings.yaml"

    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._logger = LoggerSetup.setup_logger(__name__)

    def load(self) -> Dict[str, Any]:
        """
        加载配置文件

        Returns:
            配置字典

        Raises:
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML解析错误
        """
        if self._config is not None:
            return self._config

        self._logger.debug(f"正在加载配置文件: {self.CONFIG_PATH}")

        if not os.path.exists(self.CONFIG_PATH):
            self._logger.error(f"配置文件不存在: {self.CONFIG_PATH}")
            raise FileNotFoundError(f"配置文件不存在: {self.CONFIG_PATH}")

        try:
            with open(self.CONFIG_PATH, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)

            if self._config is None:
                self._config = {}

            self._logger.info("配置文件加载成功")
            return self._config

        except yaml.YAMLError as e:
            self._logger.error(f"YAML解析错误: {e}")
            raise
        except Exception as e:
            self._logger.error(f"读取配置文件失败: {e}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项

        Args:
            key: 配置键名，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            配置值或默认值
        """
        config = self.load()
        keys = key.split(".")
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def reload(self) -> Dict[str, Any]:
        """重新加载配置文件"""
        self._config = None
        return self.load()

    @property
    def city(self) -> str:
        """获取配置的城市名称"""
        return self.get("weather.city", "北京")

    @property
    def api_key(self) -> str:
        """获取配置的API密钥"""
        return self.get("weather.api_key", "")

    @property
    def interval_value(self) -> int:
        """获取定时间隔数值"""
        return self.get("schedule.interval.value", 30)

    @property
    def interval_unit(self) -> str:
        """获取定时间隔单位"""
        return self.get("schedule.interval.unit", "minutes")

    @property
    def output_enabled(self) -> bool:
        """是否启用文件输出"""
        return self.get("output.enabled", True)

    @property
    def output_format(self) -> str:
        """获取输出格式"""
        return self.get("output.format", "txt")
