# wechat/messenger.py
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Optional

import pyautogui


@dataclass(frozen=True)
class SendOptions:
    # 发送前随机等待（减少“机器节奏”）
    pre_delay_sec_min: float = 0.6
    pre_delay_sec_max: float = 1.6

    # 输入节奏：发送前轻微扰动（可选）
    type_like_human: bool = False
    per_char_delay_min: float = 0.01
    per_char_delay_max: float = 0.03

    # 失败重试
    retries: int = 2
    retry_backoff_sec: float = 1.5

    # 发送前额外按一下 ESC，避免焦点在弹窗/搜索框
    press_esc_before_send: bool = True


def _sleep_jitter(a: float, b: float) -> None:
    time.sleep(random.uniform(a, b))


def _type_human(msg: str, per_char_min: float, per_char_max: float) -> None:
    # 用 pyautogui 模拟输入（比一次性粘贴更像人，但更慢）
    for ch in msg:
        pyautogui.typewrite(ch)
        time.sleep(random.uniform(per_char_min, per_char_max))


def send_text(wx, friend_name: str, message: str, opt: Optional[SendOptions] = None) -> None:
    """
    wx: wxauto.WeChat 实例（由 launcher.ensure_wechat_ready() 返回）
    friend_name: 唯一备注名/会话名（强烈建议唯一）
    message: 要发送的文本
    """
    opt = opt or SendOptions()

    last_err: Optional[Exception] = None
    for attempt in range(opt.retries + 1):
        try:
            # 1) 切到会话
            wx.ChatWith(friend_name)

            # 2) 轻微抖动
            _sleep_jitter(opt.pre_delay_sec_min, opt.pre_delay_sec_max)

            # 3) 确保焦点尽量在输入框
            # wxauto 的 SendMsg 通常会聚焦输入框，但偶发弹窗/焦点丢失
            if opt.press_esc_before_send:
                # pyautogui.press("esc")
                time.sleep(0.2)

            # 4) 发送
            if opt.type_like_human:
                # 先用 Ctrl+L 清空输入框不一定可靠，这里直接使用 pyautogui 输入 + Enter
                _type_human(message, opt.per_char_delay_min, opt.per_char_delay_max)
                pyautogui.press("enter")
            else:
                # wxauto 直接发送（最快、稳定）
                wx.SendMsg(message)

            return
        except Exception as e:
            last_err = e
            if attempt < opt.retries:
                time.sleep(opt.retry_backoff_sec * (attempt + 1))
            else:
                raise RuntimeError(f"发送失败：{e}") from e

    if last_err:
        raise RuntimeError(f"发送失败：{last_err}") from last_err
