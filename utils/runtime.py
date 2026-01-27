# utils/runtime.py
from __future__ import annotations

import sys
from pathlib import Path


def app_dir() -> Path:
    """
    返回程序所在目录：
    - exe：返回 exe 所在目录
    - python：返回当前脚本所在目录（项目根目录附近）
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "executable"):
        # PyInstaller 打包后
        return Path(sys.executable).resolve().parent
    # 开发态：以 main.py 所在目录为准更稳
    return Path(__file__).resolve().parents[1]
