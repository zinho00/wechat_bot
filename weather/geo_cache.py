# weather/geo_cache.py
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from .models import Location


class GeoCache:
    def __init__(self, cache_file: str = ".cache/qweather_geocode_cache.json") -> None:
        self.path = Path(cache_file)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save(self) -> None:
        try:
            self.path.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            # 缓存失败不影响主流程
            pass

    def get(self, key: str) -> Optional[Location]:
        it = self._cache.get(key)
        if not it:
            return None
        try:
            return Location(
                id=str(it["id"]),
                name=str(it["name"]),
                lat=float(it["lat"]),
                lon=float(it["lon"]),
                adm1=it.get("adm1"),
                adm2=it.get("adm2"),
                adm3=it.get("adm3"),
                tz=it.get("tz"),
            )
        except Exception:
            return None

    def set(self, key: str, loc: Location, raw: Optional[Dict[str, Any]] = None) -> None:
        payload = asdict(loc)
        if raw is not None:
            payload["raw"] = raw
        self._cache[key] = payload
        self.save()
