# weather/secrets.py
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class QWeatherSecrets:
    api_host: str
    api_key: str


def _normalize_host(host: str) -> str:
    host = host.strip()
    if not host:
        return host
    if not host.startswith("http://") and not host.startswith("https://"):
        host = "https://" + host
    # 必须 https
    if host.startswith("http://"):
        host = "https://" + host[len("http://") :]
    # 不以 / 结尾
    host = host.rstrip("/")
    return host


class QWeatherSecretsLoader:
    @staticmethod
    def load_from_env() -> Optional[QWeatherSecrets]:
        host = os.environ.get("QWEATHER_API_HOST", "").strip()
        key = os.environ.get("QWEATHER_API_KEY", "").strip()
        host = _normalize_host(host)
        if host and key:
            return QWeatherSecrets(api_host=host, api_key=key)
        return None

    @staticmethod
    def load_from_file(path: Path) -> Optional[QWeatherSecrets]:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            host = _normalize_host(str(data.get("api_host", "")).strip())
            key = str(data.get("api_key", "")).strip()
            if host and key:
                return QWeatherSecrets(api_host=host, api_key=key)
        except Exception:
            return None
        return None

    @staticmethod
    def load() -> QWeatherSecrets:
        # 优先环境变量
        env = QWeatherSecretsLoader.load_from_env()
        if env:
            return env

        # 再读 secrets.json（本地）
        secret = QWeatherSecretsLoader.load_from_file(Path("secrets.json"))
        if secret:
            return secret

        raise RuntimeError(
            "缺少和风天气配置：请设置环境变量 QWEATHER_API_HOST / QWEATHER_API_KEY，或创建 secrets.json"
        )
