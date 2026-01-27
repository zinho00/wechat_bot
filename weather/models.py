# weather/models.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    lat: float
    lon: float
    adm1: Optional[str] = None
    adm2: Optional[str] = None
    adm3: Optional[str] = None
    tz: Optional[str] = None


@dataclass(frozen=True)
class WeatherDTO:
    # 查询输入
    query_city: str

    # 解析后的地点信息
    location_id: str
    location_name: str
    adm1: Optional[str]
    adm2: Optional[str]
    adm3: Optional[str]

    # 日期
    target_date: date

    # 温度（来自 3d 预报：更适合“今天范围”）
    temp_min_c: Optional[float]
    temp_max_c: Optional[float]

    # 天气现象（来自 3d 预报）
    weather_desc: Optional[str]

    # 降雨概率（来自 24h：当天最大 POP，0~1）
    precipitation_prob: Optional[float]

    # 风（优先 now）
    wind_desc: Optional[str]
    wind_speed_mps: Optional[float]  # 可能没有，保持 None

    # 空气质量（来自 air now）
    aqi: Optional[int]
    aqi_desc: Optional[str]

    # 紫外线（来自 3d uvIndex 或 indices）
    uv_index: Optional[float]
    uv_desc: Optional[str]

    # 穿衣建议（来自 indices/1d type=3）
    clothing_advice: Optional[str]
