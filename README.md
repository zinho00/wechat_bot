# 🌤️ WeChat Weather Sender

一个运行在 **Windows 平台** 的命令行工具，用于 **每天定时向指定微信好友发送天气提醒**。  
项目采用模块化设计，支持 **自动登录检测、天气数据获取、人性化文案生成、Windows 任务计划定时执行**，并可打包为 **exe** 在无 Python 环境运行。

---

## ✨ 功能特性

- ✅ 支持 Windows 桌面版微信（UI 自动化）
- ✅ 自动检测微信登录状态（已登录自动跳过）
- ✅ 基于 **和风天气（QWeather）工程版 API**
- ✅ 城市名 → Location ID 自动解析并缓存
- ✅ 当天天气 / 温度区间 / 降雨概率 / 风力 / 紫外线 / 穿衣建议
- ✅ 人性化消息生成（模板可编辑，支持随机化）
- ✅ Windows 任务计划程序定时执行（稳定、不常驻）
- ✅ 可打包为 exe，目标机器无需安装 Python

---

## 🖥️ 运行环境

- 操作系统：Windows 10 / Windows 11
- 微信：Windows 桌面版（已登录）！！！需要特定版本的微信，自行下载 3.9.12版本
- 网络：可访问和风天气 API Host
- （源码运行）Python ≥ 3.9  
- （exe 运行）❌ 不需要 Python

---

## 📁 项目结构

weather_sender/
├── main.py # 主入口（三段式编排）
├── wechat/ # 微信相关（启动 / 登录 / 发送）
├── weather/ # 和风天气数据获取
├── message/ # 人性化消息生成
├── utils/ # 通用工具
├── templates.json # 文案模板（外置，可随时修改）
├── config.ini # 本地配置（不提交）
├── secrets.json # API 密钥（不提交）
├── run_daily.bat # 定时任务入口
├── install_task.bat # 安装任务计划
├── uninstall_task.bat # 删除任务计划
└── README.md

---

## 🔐 配置说明（重要）

### 1️⃣ 和风天气密钥（必需）

创建 `secrets.json`（已在 `.gitignore` 中）：

```json
{
  "api_host": "https://YOUR_HOST.re.qweatherapi.com",
  "api_key": "YOUR_API_KEY"
}

2️⃣ 本地配置文件

创建 config.ini：

[wechat]
wechat_path = C:\Program Files (x86)\Tencent\WeChat\WeChat.exe
friend_name = 文件传输助手

[weather]
city = 北京市朝阳区

3️⃣ 文案模板（可随时修改）

templates.json（放在 exe 同级目录）：

{
  "greetings": [
    "早上好～",
    "今日天气播报来啦 ☀️"
  ],
  "notices": [
    "出门注意安全",
    "记得多喝水"
  ],
  "tails": [
    "— 自动天气播报"
  ]
}

▶️ 运行方式
方式一：源码运行（开发/调试）
pip install -r requirements.txt
python main.py

方式二：exe 运行（推荐）
weather_sender.exe


exe 同级目录必须包含：

config.ini

secrets.json

templates.json
