import re
from typing import Any, Dict, List, Optional, Tuple

from logger_setup import LoggerSetup


class ValidationError(Exception):
    """数据校验错误异常"""
    pass


class ConfigValidator:
    """配置校验器"""

    VALID_INTERVAL_UNITS = ["minutes", "hours"]
    MIN_INTERVAL_VALUE = 1
    MAX_INTERVAL_VALUE = 1440

    def __init__(self):
        self._logger = LoggerSetup.setup_logger(__name__)
        self._errors: List[str] = []

    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        校验配置完整性

        Args:
            config: 配置字典

        Returns:
            (是否通过, 错误列表)
        """
        self._errors = []

        if not isinstance(config, dict):
            self._errors.append("配置必须是字典类型")
            return False, self._errors

        self._validate_weather_section(config)
        self._validate_schedule_section(config)
        self._validate_output_section(config)

        if self._errors:
            self._logger.warning(f"配置校验失败: {self._errors}")
            return False, self._errors

        self._logger.info("配置校验通过")
        return True, []

    def _validate_weather_section(self, config: Dict[str, Any]) -> None:
        """校验weather配置节"""
        weather = config.get("weather", {})

        if not isinstance(weather, dict):
            self._errors.append("weather配置必须是字典类型")
            return

        city = weather.get("city", "")
        if not city:
            self._errors.append("weather.city不能为空")
        elif not isinstance(city, str):
            self._errors.append("weather.city必须是字符串")
        elif len(city) > 50:
            self._errors.append("weather.city长度不能超过50个字符")

        api_key = weather.get("api_key", "")
        if not isinstance(api_key, str):
            self._errors.append("weather.api_key必须是字符串")

    def _validate_schedule_section(self, config: Dict[str, Any]) -> None:
        """校验schedule配置节"""
        schedule = config.get("schedule", {})

        if not isinstance(schedule, dict):
            self._errors.append("schedule配置必须是字典类型")
            return

        interval = schedule.get("interval", {})
        if not isinstance(interval, dict):
            self._errors.append("schedule.interval必须是字典类型")
            return

        value = interval.get("value")
        if value is None:
            self._errors.append("schedule.interval.value不能为空")
        elif not isinstance(value, int):
            self._errors.append("schedule.interval.value必须是整数")
        elif value < self.MIN_INTERVAL_VALUE or value > self.MAX_INTERVAL_VALUE:
            self._errors.append(
                f"schedule.interval.value必须在{self.MIN_INTERVAL_VALUE}-{self.MAX_INTERVAL_VALUE}之间"
            )

        unit = interval.get("unit", "")
        if not unit:
            self._errors.append("schedule.interval.unit不能为空")
        elif unit not in self.VALID_INTERVAL_UNITS:
            self._errors.append(
                f"schedule.interval.unit必须是以下值之一: {self.VALID_INTERVAL_UNITS}"
            )

    def _validate_output_section(self, config: Dict[str, Any]) -> None:
        """校验output配置节"""
        output = config.get("output", {})

        if not isinstance(output, dict):
            self._errors.append("output配置必须是字典类型")
            return

        enabled = output.get("enabled")
        if enabled is not None and not isinstance(enabled, bool):
            self._errors.append("output.enabled必须是布尔值")

        fmt = output.get("format", "txt")
        if fmt not in ["txt"]:
            self._errors.append("output.format当前仅支持txt格式")


class WeatherDataValidator:
    """天气数据校验器"""

    REQUIRED_FIELDS = ["temperature", "humidity", "condition", "wind_direction"]

    def __init__(self):
        self._logger = LoggerSetup.setup_logger(__name__)

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        校验天气数据完整性

        Args:
            data: 天气数据字典

        Returns:
            (是否通过, 错误信息)
        """
        if not isinstance(data, dict):
            return False, "天气数据必须是字典类型"

        missing_fields = []
        for field in self.REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            return False, f"天气数据缺少必需字段: {missing_fields}"

        temp = data.get("temperature")
        if temp is not None:
            try:
                float(temp)
            except (ValueError, TypeError):
                return False, f"temperature必须是数值类型: {temp}"

        humidity = data.get("humidity")
        if humidity is not None:
            try:
                hum_val = float(humidity)
                if hum_val < 0 or hum_val > 100:
                    return False, f"humidity必须在0-100之间: {humidity}"
            except (ValueError, TypeError):
                return False, f"humidity必须是数值类型: {humidity}"

        self._logger.debug("天气数据校验通过")
        return True, None


class CityNameValidator:
    """城市名称校验器"""

    def __init__(self):
        self._logger = LoggerSetup.setup_logger(__name__)

    def validate(self, city_name: str) -> Tuple[bool, Optional[str]]:
        """
        校验城市名称合法性

        Args:
            city_name: 城市名称

        Returns:
            (是否通过, 错误信息)
        """
        if not city_name:
            return False, "城市名称不能为空"

        if not isinstance(city_name, str):
            return False, "城市名称必须是字符串"

        if len(city_name) > 50:
            return False, "城市名称长度不能超过50个字符"

        if re.search(r'[<>"\'&]', city_name):
            return False, "城市名称包含非法字符"

        return True, None
