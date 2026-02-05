# wechat/launcher.py
from __future__ import annotations

import configparser
import subprocess
import time
from dataclasses import dataclass
from typing import Optional

import psutil
import pyautogui
from wxauto import WeChat


@dataclass(frozen=True)
class WeChatReadyOptions:
    login_timeout_sec: int = 120
    press_enter_interval_sec: int = 15
    launch_wait_sec: int = 4
    # 已登录检测：连续成功次数（降低偶发空列表误判）
    logged_in_confirm_times: int = 2
    logged_in_confirm_interval_sec: float = 0.6


def _is_wechat_process_running() -> bool:
    for proc in psutil.process_iter(["name"]):
        try:
            if (proc.info.get("name") or "").lower() == "wechat.exe":
                return True
        except Exception:
            continue
    return False


def _launch_wechat(exe_path: str, opt: WeChatReadyOptions) -> None:
    # 微信未运行才启动
    subprocess.Popen([exe_path], shell=False)
    time.sleep(opt.launch_wait_sec)


def _try_get_wechat_if_logged_in(opt: WeChatReadyOptions) -> Optional[WeChat]:
    """
    尝试判断微信是否已登录：
    - 能成功构造 WeChat()
    - 且能获取到会话列表（GetSessionList 不为空）
    为避免启动瞬间或 UI 未就绪导致误判，做连续确认。
    """
    ok = 0
    wx_obj: Optional[WeChat] = None

    for _ in range(opt.logged_in_confirm_times):
        try:
            wx = WeChat()
            sessions = wx.GetSessionList()
            if sessions:
                ok += 1
                wx_obj = wx
            else:
                ok = 0
        except Exception:
            ok = 0
        time.sleep(opt.logged_in_confirm_interval_sec)

    if ok >= opt.logged_in_confirm_times and wx_obj is not None:
        return wx_obj
    return None


def _wait_for_login(opt: WeChatReadyOptions) -> WeChat:
    """
    未登录时进入等待：
    - 每隔 press_enter_interval_sec 按一次 Enter（触发登录）
    - 超时则报错
    """
    start = time.time()
    last_press = 0.0

    print("[INFO] 等待微信登录...（将自动尝试按 Enter 触发登录）")
    while time.time() - start < opt.login_timeout_sec:
        # 先尝试检测是否已登录
        wx = _try_get_wechat_if_logged_in(opt)
        if wx:
            print("[INFO] 微信已登录（检测通过）。")
            return wx

        # 定期按 Enter
        now = time.time()
        if now - last_press >= opt.press_enter_interval_sec:
            print("[ACTION] 尝试按下 Enter 触发登录...")
            pyautogui.press("enter")
            last_press = now

        time.sleep(0.8)

    raise RuntimeError("等待超时：微信未登录或窗口不可用。请确认微信可正常登录。")


def ensure_wechat_ready(config_path: str = "config.ini", opt: Optional[WeChatReadyOptions] = None) -> WeChat:
    """
    入口函数：确保返回一个“可用且已登录”的 wxauto.WeChat 实例
    
    - 如果已登录：直接返回（跳过启动与按 Enter）
    - 如果未运行：启动
    - 如果运行但未登录：等待并自动按 Enter
    """
    opt = opt or WeChatReadyOptions()

    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding="utf-8")

    exe_path = cfg.get("wechat", "wechat_path", fallback="").strip()
    if not exe_path:
        raise RuntimeError("config.ini 缺少 [wechat] wechat_path 配置。")

    # 1) 若已登录，直接返回（关键：跳过登录步骤）
    wx = _try_get_wechat_if_logged_in(opt)
    if wx:
        print("[INFO] 检测到微信已登录，跳过登录步骤。")
        return wx

    # 2) 未登录：若进程未运行则启动
    if not _is_wechat_process_running():
        print("[INFO] 微信未运行，正在启动微信...")
        _launch_wechat(exe_path, opt)
    else:
        print("[INFO] 微信进程已运行，但未检测到登录态，进入登录等待...")

    # 3) 等待登录并返回
    return _wait_for_login(opt)
