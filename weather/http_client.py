# weather/http_client.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


class QWeatherHTTPError(RuntimeError):
    pass


@dataclass
class QWeatherHttpClient:
    api_host: str
    api_key: str
    timeout_sec: int = 15
    user_agent: str = "weather_sender/1.0"

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.api_host}{path}"
        p = dict(params or {})
        # API KEY 模式：统一加 key
        p["key"] = self.api_key

        resp = self.session.get(url, params=p, timeout=self.timeout_sec)
        if resp.status_code != 200:
            raise QWeatherHTTPError(f"HTTP {resp.status_code} {url}: {resp.text[:300]}")
        data = resp.json()
        code = str(data.get("code", ""))
        if code and code != "200":
            raise QWeatherHTTPError(f"QWeather code={code} {url}: {data}")
        return data
