# weather/qweather_provider.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from .geo_cache import GeoCache
from .http_client import QWeatherHttpClient, QWeatherHTTPError
from .models import Location, WeatherDTO
from .secrets import QWeatherSecretsLoader


def _parse_iso_dt(s: str) -> datetime:
    # e.g. "2021-02-16T15:00+08:00"
    return datetime.fromisoformat(s)


def _simplify_place_name(name: str) -> str:
    simplified = name.replace(" ", "")
    for suffix in ("自治州", "地区", "省", "市", "区", "县", "旗", "盟", "州"):
        simplified = simplified.replace(suffix, "")
    return simplified


def _pick_best_location(query: str, locs: List[Dict[str, Any]]) -> Dict[str, Any]:
    query_raw = query.replace(" ", "")
    query_simple = _simplify_place_name(query_raw)
    prefers_district = any(s in query_raw for s in ("区", "县", "旗"))

    def score(loc: Dict[str, Any]) -> Tuple[int, int]:
        name = str(loc.get("name", "")).strip()
        adm1 = str(loc.get("adm1", "")).strip()
        adm2 = str(loc.get("adm2", "")).strip()
        adm3 = str(loc.get("adm3", "")).strip()

        sc = 0
        if name == query_raw:
            sc += 100
        if name and name in query_raw:
            sc += 60
        if _simplify_place_name(name) == query_simple:
            sc += 50
        if name and _simplify_place_name(name) in query_simple:
            sc += 30

        for adm in (adm1, adm2, adm3):
            if not adm:
                continue
            if adm in query_raw:
                sc += 8
            if _simplify_place_name(adm) in query_simple:
                sc += 5

        if prefers_district and name.endswith(("区", "县", "旗")):
            sc += 15

        if adm3:
            sc += 4

        return sc, len(name)

    return max(locs, key=score)


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except Exception:
        return None


def _safe_int(v: Any) -> Optional[int]:
    try:
        if v is None or v == "":
            return None
        return int(float(v))
    except Exception:
        return None


def _aqi_desc_cn(aqi: Optional[int]) -> Optional[str]:
    if aqi is None:
        return None
    if aqi <= 50:
        return "优"
    if aqi <= 100:
        return "良"
    if aqi <= 150:
        return "轻度污染"
    if aqi <= 200:
        return "中度污染"
    if aqi <= 300:
        return "重度污染"
    return "严重污染"


def _uv_desc_cn(uv: Optional[float]) -> Optional[str]:
    if uv is None:
        return None
    if uv < 3:
        return f"{uv:.0f}（低）"
    if uv < 6:
        return f"{uv:.0f}（中等）"
    if uv < 8:
        return f"{uv:.0f}（较高）"
    if uv < 11:
        return f"{uv:.0f}（高）"
    return f"{uv:.0f}（极高）"


def _today_pop_pct(hourly: List[Dict[str, Any]], strategy: str = "max") -> int:
    if not hourly:
        return 0

    # 以第一条小时预报的日期作为“今天”
    try:
        first_dt = _parse_iso_dt(hourly[0]["fxTime"])
        first_date = first_dt.date()
    except Exception:
        pops: List[int] = []
        for h in hourly:
            p = _safe_int(h.get("pop"))
            if p is not None:
                pops.append(p)
        return max(pops) if pops else 0

    pops: List[int] = []
    for h in hourly:
        try:
            dt = _parse_iso_dt(h["fxTime"])
        except Exception:
            continue
        if dt.date() != first_date:
            break
        p = _safe_int(h.get("pop"))
        if p is not None:
            pops.append(p)

    if not pops:
        return 0

    s = (strategy or "max").lower().strip()
    if s == "avg":
        return int(round(sum(pops) / len(pops)))
    return max(pops)


@dataclass
class QWeatherProvider:
    """
    第二部分核心：城市 -> Location(缓存) -> 组合接口 -> WeatherDTO

    重要：Host 与 Key 强绑定，因此所有接口默认走同一个 api_host。
    """
    city_range: str = "cn"
    pop_strategy: str = "max"
    indices_types: Optional[Dict[str, str]] = None  # {"clothing":"3","uv":"5"} 等
    cache_file: str = ".cache/qweather_geocode_cache.json"

    def __post_init__(self) -> None:
        secrets = QWeatherSecretsLoader.load()
        self.client = QWeatherHttpClient(api_host=secrets.api_host, api_key=secrets.api_key)
        self.geo_cache = GeoCache(self.cache_file)

    # ---------- public ----------
    def get_today_weather(self, city: str) -> WeatherDTO:
        loc = self._city_lookup(city)

        now = self._get("/v7/weather/now", {"location": loc.id})
        daily3d = self._get("/v7/weather/3d", {"location": loc.id})
        hourly24h = self._get("/v7/weather/24h", {"location": loc.id})

        # 空气质量（可能账号未开通；出错则置空）
        air = None
        try:
            air = self._get("/v7/air/now", {"location": loc.id})
        except QWeatherHTTPError:
            air = None

        # 生活指数（按需）
        indices = None
        indices_types = self.indices_types or {"clothing": "3", "uv": "5"}
        type_csv = ",".join([v for v in indices_types.values() if v])
        if type_csv:
            try:
                indices = self._get("/v7/indices/1d", {"location": loc.id, "type": type_csv})
            except QWeatherHTTPError:
                indices = None

        return self._build_dto(
            query_city=city,
            loc=loc,
            now=now,
            daily3d=daily3d,
            hourly24h=hourly24h,
            air=air,
            indices=indices,
        )

    # ---------- endpoints ----------
    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.get_json(path, params)

    def _city_lookup(self, city_name: str) -> Location:
        key = city_name.strip()
        cached = self.geo_cache.get(key)
        if cached:
            return cached

        # 推荐：/geo/v2/city/lookup
        data = self._get(
            "/geo/v2/city/lookup",
            {"location": key, "range": self.city_range, "number": 10},
        )
        locs = data.get("location") or []
        if not locs:
            raise RuntimeError(f"Geo lookup empty for '{city_name}', data={data}")

        best = _pick_best_location(key, locs)
        loc = Location(
            id=str(best["id"]),
            name=str(best.get("name", key)),
            lat=float(best["lat"]),
            lon=float(best["lon"]),
            adm1=best.get("adm1"),
            adm2=best.get("adm2"),
            adm3=best.get("adm3"),
            tz=best.get("tz"),
        )
        self.geo_cache.set(key, loc, raw=best)
        return loc

    # ---------- dto build ----------
    def _build_dto(
        self,
        *,
        query_city: str,
        loc: Location,
        now: Dict[str, Any],
        daily3d: Dict[str, Any],
        hourly24h: Dict[str, Any],
        air: Optional[Dict[str, Any]],
        indices: Optional[Dict[str, Any]],
    ) -> WeatherDTO:
        # 3d 的第一天作为“今天”
        daily_list = daily3d.get("daily") or []
        today = daily_list[0] if daily_list else {}

        fx_date_str = str(today.get("fxDate", "")).strip()
        target_date = date.fromisoformat(fx_date_str) if fx_date_str else datetime.now().date()

        temp_min = _safe_float(today.get("tempMin"))
        temp_max = _safe_float(today.get("tempMax"))

        text_day = str(today.get("textDay", "")).strip()
        text_night = str(today.get("textNight", "")).strip()
        if text_day and text_night and text_day != text_night:
            weather_desc = f"{text_day}转{text_night}"
        else:
            weather_desc = text_day or text_night or None

        # POP：取“今天”的小时最大值
        hourly_list = hourly24h.get("hourly") or []
        pop_pct = _today_pop_pct(hourly_list, strategy=self.pop_strategy)
        precipitation_prob = None
        if pop_pct is not None:
            precipitation_prob = max(0.0, min(1.0, float(pop_pct) / 100.0))

        # wind：优先 now
        now_obj = now.get("now") or {}
        wind_dir = str(now_obj.get("windDir", "")).strip()
        wind_scale = str(now_obj.get("windScale", "")).strip()
        wind_desc = None
        if wind_dir or wind_scale:
            wind_desc = " ".join([x for x in [wind_dir, f"{wind_scale}级" if wind_scale else ""] if x]).strip()
        else:
            wdir = str(today.get("windDirDay", "")).strip()
            wsc = str(today.get("windScaleDay", "")).strip()
            wind_desc = " ".join([x for x in [wdir, f"{wsc}级" if wsc else ""] if x]).strip() or None

        # wind speed m/s：接口不一定提供，工程化兜底
        wind_speed_mps = _safe_float(now_obj.get("windSpeed"))

        # AQI（v7/air/now）
        aqi = None
        aqi_desc = None
        if air:
            aqi = _safe_int((air.get("now") or {}).get("aqi"))
            aqi_desc = _aqi_desc_cn(aqi)

        # UV：优先 3d 的 uvIndex
        uv_index = _safe_float(today.get("uvIndex"))
        uv_desc = _uv_desc_cn(uv_index)

        # indices：穿衣(3) 紫外线(5)等
        clothing_advice = None
        if indices:
            for it in (indices.get("daily") or []):
                name = str(it.get("name", "")).strip()
                typ = str(it.get("type", "")).strip()
                text = str(it.get("text") or it.get("detail") or it.get("category") or "").strip()
                if typ == "3" or ("穿衣" in name):
                    clothing_advice = text or None
                if (uv_index is None) and (typ == "5" or ("紫外线" in name)):
                    # 有些账号 indices 会给紫外线等级描述
                    # uv_index 无法保证有数值，这里就直接用文字描述放到 uv_desc
                    if text:
                        uv_desc = text

        return WeatherDTO(
            query_city=query_city,
            location_id=loc.id,
            location_name=loc.name,
            adm1=loc.adm1,
            adm2=loc.adm2,
            adm3=loc.adm3,
            target_date=target_date,
            temp_min_c=temp_min,
            temp_max_c=temp_max,
            weather_desc=weather_desc,
            precipitation_prob=precipitation_prob,
            wind_desc=wind_desc,
            wind_speed_mps=wind_speed_mps,
            aqi=aqi,
            aqi_desc=aqi_desc,
            uv_index=uv_index,
            uv_desc=uv_desc,
            clothing_advice=clothing_advice,
        )
