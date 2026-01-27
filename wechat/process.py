# wechat/process.py
from __future__ import annotations

import time
import psutil


def close_wechat_soft() -> None:
    """
    温和方式：尝试关闭主窗口（wxauto 不一定提供 close）。
    这里留给你后续扩展：可以用 win32gui/pywinauto 发送 WM_CLOSE。
    当前版本先不做强制关闭，避免误杀/风控。
    """
    # 作为“温和关闭”的占位：默认什么都不做
    return


def kill_wechat_hard() -> None:
    """
    强制杀进程（不推荐）：可能更像异常行为，且会中断微信的正常状态。
    仅在你明确需要“每次运行都退出”时使用。
    """
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if (proc.info.get("name") or "").lower() == "wechat.exe":
                proc.kill()
        except Exception:
            pass
    time.sleep(1)
