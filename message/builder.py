# message/builder.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from weather.models import WeatherDTO
from .config import MessageConfig
from .templates import load_templates, pick_greeting, pick_notice, pick_tail


class MessageBuilder:
    def __init__(self, cfg: MessageConfig) -> None:
        self.cfg = cfg
        self.templates = load_templates(cfg.templates_path)

    @staticmethod
    def _fmt_prob(prob: Optional[float]) -> str:
        if prob is None:
            return "暂无"
        prob = max(0.0, min(1.0, float(prob)))
        return f"{int(round(prob * 100))}%"

    @staticmethod
    def _weather_tips(w: WeatherDTO) -> List[str]:
        tips: List[str] = []

        # 1) 低温提醒
        if w.temp_min_c is not None and w.temp_min_c <= 10:
            tips.append("今天气温偏低，出门注意保暖，可带个暖宝宝")
            
        if w.temp_max_c is not None and w.temp_max_c  > 15 < 25:
            tips.append("温度刚刚好，不用穿太厚")

        # 2) 高温提醒
        if w.temp_max_c is not None and w.temp_max_c >= 25:
            tips.append("天气较热，注意防晒补水")

        # 3) 降雨提醒（优先天气现象包含“雨”，否则用 POP）
        desc = (w.weather_desc or "")
        if "雨" in desc:
            tips.append("今天有雨，出门记得带伞")
        else:
            if w.precipitation_prob is not None and w.precipitation_prob >= 0.3:
                tips.append("今天可能有雨，建议备一把折叠伞")

        # 4) 大风提醒（文字启发式）
        wind_desc = (w.wind_desc or "")
        # windScale 常是“X级”，我们在 provider 已拼成“xx风 X级”
        # 做个启发式：>=5级给提醒
        import re
        m = re.search(r"(\d+)\s*级", wind_desc)
        if m:
            try:
                scale = int(m.group(1))
                if scale >= 5:
                    tips.append("风力较大，注意防风，骑行请注意安全")
            except Exception:
                pass

        # 5) 紫外线提醒（优先 uv_desc，其次 uv_index）
        if w.uv_index is not None and w.uv_index >= 6:
            tips.append("紫外线较强，外出建议做好防晒（帽子/防晒霜）")
        elif (w.uv_desc or "").find("高") != -1 or (w.uv_desc or "").find("较高") != -1:
            tips.append("紫外线偏强，外出建议做好防晒")

        # 6) 空气质量提醒（如启用 AQI）
        if w.aqi is not None and w.aqi > 150:
            tips.append("空气质量较差，建议减少剧烈运动，必要时佩戴口罩")

        return tips

    def build(self, w: WeatherDTO) -> str:
        enabled = set(self.cfg.normalized_enabled())

        header = pick_greeting(self.cfg.randomize, self.templates)
        lines: List[str] = [header, "前方杨记者带来报导——"]

        # meta：地点/日期（你可以只保留地点不显示 id）
        if "meta" in enabled:
            place = w.query_city
            # 显示更稳：省/市/区（若存在）
            parts = [p for p in [w.adm1, w.adm2, w.location_name] if p]
            if parts:
                place = f"{w.query_city}（定位：{'/'.join(parts)}）"
            lines.append(place)
            lines.append(f"日期：{w.target_date.isoformat()}")

        # 1) 温度范围
        if "temperature" in enabled:
            if w.temp_min_c is None or w.temp_max_c is None:
                lines.append("今天南山气温：暂无")
            else:
                lines.append(f"今天南山气温：{w.temp_min_c:.0f}°C ~ {w.temp_max_c:.0f}°C")

        # 2) 天气现象
        if "weather" in enabled:
            lines.append(f"天气：{(w.weather_desc or '暂无').strip()}")

        # 3) 降雨概率
        if "precipitation" in enabled:
            lines.append(f"降雨概率：{self._fmt_prob(w.precipitation_prob)}")

        # 插入 tips（人性化提醒）
        tips = self._weather_tips(w)
        lines.extend(tips)

        # 4) 风力（兼容风速 None）
        if "wind" in enabled:
            wind_desc = (w.wind_desc or "暂无").strip()
            if w.wind_speed_mps is not None:
                try:
                    lines.append(f"风力：{wind_desc}（{float(w.wind_speed_mps):.1f} m/s）")
                except Exception:
                    lines.append(f"风力：{wind_desc}")
            else:
                lines.append(f"风力：{wind_desc}")

        # 5) 空气质量
        if "air_quality" in enabled:
            if w.aqi is None:
                lines.append("空气质量：暂无")
            else:
                suffix = f"（{w.aqi_desc}）" if w.aqi_desc else ""
                lines.append(f"空气质量：AQI {w.aqi}{suffix}")

        # 6) 紫外线
        if "uv" in enabled:
            if w.uv_desc and w.uv_desc.strip() and w.uv_desc.strip() != "暂无":
                lines.append(f"紫外线：{w.uv_desc.strip()}")
            elif w.uv_index is not None:
                lines.append(f"紫外线：{w.uv_index:.0f}")
            else:
                lines.append("紫外线：暂无")

        # 7) 穿衣建议
        if "clothing" in enabled:
            advice = (w.clothing_advice or "").strip()
            lines.append(f"穿衣建议：{advice if advice else '暂无'}")

        notice = pick_notice(self.cfg.randomize, self.templates)
        if notice:
            lines.append(notice)

        tail = pick_tail(self.cfg.randomize, self.templates)
        if tail:
            lines.append(tail)

        return "\n".join([x for x in lines if str(x).strip()]).strip()
