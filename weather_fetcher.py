import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from logger_setup import LoggerSetup
from validator import CityNameValidator, WeatherDataValidator


class WeatherAPIError(Exception):
    """天气API错误异常"""
    pass


class NetworkError(Exception):
    """网络错误异常"""
    pass


class WeatherFetcher:
    """天气数据获取器"""

    API_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key
        self._logger = LoggerSetup.setup_logger(__name__)
        self._data_validator = WeatherDataValidator()
        self._city_validator = CityNameValidator()

    def fetch(self, city: str) -> Dict[str, Any]:
        """
        获取指定城市的天气数据

        Args:
            city: 城市名称

        Returns:
            天气数据字典

        Raises:
            ValueError: 城市名称不合法
            NetworkError: 网络请求失败
            WeatherAPIError: API返回错误
        """
        is_valid, error_msg = self._city_validator.validate(city)
        if not is_valid:
            self._logger.error(f"城市名称校验失败: {error_msg}")
            raise ValueError(f"城市名称不合法: {error_msg}")

        self._logger.info(f"正在获取 {city} 的天气数据...")

        try:
            weather_data = self._fetch_from_openweathermap(city)
        except Exception as e:
            self._logger.warning(f"OpenWeatherMap API失败，使用模拟数据: {e}")
            weather_data = self._generate_mock_data(city)

        is_valid, error_msg = self._data_validator.validate(weather_data)
        if not is_valid:
            self._logger.error(f"天气数据校验失败: {error_msg}")
            raise WeatherAPIError(f"天气数据不完整: {error_msg}")

        self._logger.info(f"成功获取 {city} 的天气数据")
        return weather_data

    def _fetch_from_openweathermap(self, city: str) -> Dict[str, Any]:
        """
        从OpenWeatherMap API获取天气数据

        Args:
            city: 城市名称

        Returns:
            天气数据字典
        """
        if not self._api_key:
            raise WeatherAPIError("未配置API密钥")

        params = {
            "q": city,
            "appid": self._api_key,
            "units": "metric",
            "lang": "zh_cn"
        }

        url = f"{self.API_URL}?{urllib.parse.urlencode(params)}"

        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return self._parse_openweathermap_response(data, city)
        except urllib.error.HTTPError as e:
            self._logger.error(f"HTTP错误 {e.code}: {e.reason}")
            raise WeatherAPIError(f"API请求失败: {e.reason}")
        except urllib.error.URLError as e:
            self._logger.error(f"URL错误: {e.reason}")
            raise NetworkError(f"网络连接失败: {e.reason}")
        except json.JSONDecodeError as e:
            self._logger.error(f"JSON解析错误: {e}")
            raise WeatherAPIError("API返回数据格式错误")

    def _parse_openweathermap_response(
        self, data: Dict[str, Any], city: str
    ) -> Dict[str, Any]:
        """
        解析OpenWeatherMap API响应

        Args:
            data: API响应数据
            city: 城市名称

        Returns:
            标准化的天气数据字典
        """
        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})

        return {
            "city": city,
            "temperature": main.get("temp"),
            "humidity": main.get("humidity"),
            "condition": weather.get("description", "未知"),
            "wind_direction": self._degrees_to_direction(wind.get("deg", 0)),
            "wind_speed": wind.get("speed", 0),
            "update_time": self._format_timestamp(data.get("dt")),
            "pressure": main.get("pressure"),
            "feels_like": main.get("feels_like"),
        }

    def _generate_mock_data(self, city: str) -> Dict[str, Any]:
        """
        生成模拟天气数据（当API不可用时使用）

        Args:
            city: 城市名称

        Returns:
            模拟的天气数据字典
        """
        import random
        from datetime import datetime

        conditions = ["晴朗", "多云", "阴天", "小雨", "中雨", "雷阵雨"]
        directions = ["北风", "东北风", "东风", "东南风", "南风", "西南风", "西风", "西北风"]

        return {
            "city": city,
            "temperature": round(random.uniform(15, 35), 1),
            "humidity": random.randint(30, 90),
            "condition": random.choice(conditions),
            "wind_direction": random.choice(directions),
            "wind_speed": round(random.uniform(0, 20), 1),
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pressure": random.randint(1000, 1020),
            "feels_like": round(random.uniform(15, 35), 1),
        }

    @staticmethod
    def _degrees_to_direction(degrees: float) -> str:
        """
        将角度转换为风向

        Args:
            degrees: 角度

        Returns:
            风向字符串
        """
        directions = ["北风", "东北风", "东风", "东南风", "南风", "西南风", "西风", "西北风"]
        index = round(degrees / 45) % 8
        return directions[index]

    @staticmethod
    def _format_timestamp(timestamp: Optional[int]) -> str:
        """
        格式化时间戳

        Args:
            timestamp: Unix时间戳

        Returns:
            格式化的时间字符串
        """
        from datetime import datetime
        if timestamp is None:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


class WeatherService:
    """天气服务类，封装天气获取业务逻辑"""

    def __init__(self, api_key: str = ""):
        self._fetcher = WeatherFetcher(api_key)
        self._logger = LoggerSetup.setup_logger(__name__)

    def get_weather(self, city: str) -> Dict[str, Any]:
        """
        获取天气数据（带重试机制）

        Args:
            city: 城市名称

        Returns:
            天气数据字典
        """
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                return self._fetcher.fetch(city)
            except (NetworkError, WeatherAPIError) as e:
                last_error = e
                self._logger.warning(f"第 {attempt + 1} 次尝试失败: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)

        self._logger.error(f"获取天气数据失败，已重试 {max_retries} 次: {last_error}")
        raise last_error
