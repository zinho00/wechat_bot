# message/config.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
import sys


def app_dir() -> Path:
    """
    返回程序所在目录：
    - exe：exe 所在目录
    - python：项目根目录（以当前文件向上两级推断）
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "executable"):
        return Path(sys.executable).resolve().parent
    # message/config.py -> message -> 项目根目录
    return Path(__file__).resolve().parents[1]


def default_templates_path() -> str:
    # 强制从程序所在目录读取 templates.json（exe 同级）
    return str(app_dir() / "templates.json")


@dataclass(frozen=True)
class MessageConfig:
    randomize: bool = True
    enabled_fields: List[str] | None = None

    # ✅ 改这里：不再指向 message/templates.json
    templates_path: str = default_templates_path()

    def normalized_enabled(self) -> List[str]:
        if not self.enabled_fields:
            return [
                "meta",
                "temperature",
                "weather",
                "precipitation",
                "wind",
                "uv",
                "clothing",
            ]
        return self.enabled_fields
