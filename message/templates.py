# message/templates.py
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Templates:
    greetings: List[str]
    openings: List[str]
    notices: List[str]
    tails: List[str]

from pathlib import Path
import os


def load_templates(path: str) -> Templates:
    print(f"[DEBUG] cwd={Path.cwd()}")
    print(f"[DEBUG] try_templates_path={Path(path).resolve()}")
    print(f"[DEBUG] exists={Path(path).exists()}")
    
    p = Path(path)
    if not p.exists():
        # 没有模板文件也能跑：提供默认模板
        return Templates(
            greetings=["早上好"],
            notices=["祝你今天顺利！"],
            tails=["-默认模板"],
        )

    data = json.loads(p.read_text(encoding="utf-8"))
    return Templates(
        greetings=list(data.get("greetings", []) or []),
        openings=data.get("openings", []),
        notices=list(data.get("notices", []) or []),
        tails=list(data.get("tails", []) or []),
    )


def _pick(randomize: bool, items: List[str]) -> str:
    if not items:
        return ""
    if randomize:
        return random.choice(items).strip()
    return str(items[0]).strip()


def pick_greeting(randomize: bool, t: Templates) -> str:
    return _pick(randomize, t.greetings)

def pick_opening(randomize: bool, t: Templates) -> str:
    return _pick(randomize, t.openings)

def pick_notice(randomize: bool, t: Templates) -> str:
    return _pick(randomize, t.notices)

def pick_tail(randomize: bool, t: Templates) -> str:
    return _pick(randomize, t.tails)
