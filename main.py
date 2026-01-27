# main.py
from __future__ import annotations

import configparser

from wechat.launcher import ensure_wechat_ready
from wechat.messenger import send_text, SendOptions
from wechat.process import close_wechat_soft, kill_wechat_hard

from weather.qweather_provider import QWeatherProvider
from message.builder import MessageBuilder
from message.config import MessageConfig


def load_wechat_friend(config_path: str = "config.ini") -> str:
    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding="utf-8")
    return cfg.get("wechat", "friend_name")


def load_city(config_path: str = "config.ini") -> str:
    cfg = configparser.ConfigParser()
    cfg.read(config_path, encoding="utf-8")
    return cfg.get("weather", "city")


def main() -> None:
    # 1) 第一部分：微信启动/登录/初始化
    wx = ensure_wechat_ready()

    # 2) 第二部分：取天气 DTO + 生成人性化消息
    city = load_city()
    provider = QWeatherProvider(city_range="cn", pop_strategy="max")
    dto = provider.get_today_weather(city)

    # ✅ 关键改动：不要再手动指定 templates_path
    # templates.json 将从 exe 同级目录读取（MessageConfig 默认值控制）
    msg_cfg = MessageConfig(
        randomize=True,
        enabled_fields=[
            # "meta",
            "temperature",
            "weather",
            "precipitation",
            "wind",
            "uv",
            # "clothing",
            # "air_quality",
        ],
    )

    builder = MessageBuilder(msg_cfg)
    text = builder.build(dto)

    # 3) 第三部分：发送
    friend_name = load_wechat_friend()
    send_opt = SendOptions(
        pre_delay_sec_min=0.6,
        pre_delay_sec_max=1.6,
        type_like_human=False,
        retries=2,
        retry_backoff_sec=1.5,
        press_esc_before_send=True,
    )
    send_text(wx, friend_name, text, send_opt)

    # 4) 可选：退出微信
    # close_wechat_soft()
    kill_wechat_hard()


if __name__ == "__main__":
    main()
