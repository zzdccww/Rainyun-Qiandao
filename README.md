# 雨云自动签到（GHA 版）

雨云每日自动签到工具，使用 GitHub Actions 定时运行，支持单账号签到、服务器到期检测与自动续费，并通过 Telegram 通知结果。

> WebUI 已移除，配置统一通过 GitHub Secrets 传入。

## 功能特性

- 单账号签到（用户名/密码）
- 服务器到期检查与自动续费（API Key 可选）
- Telegram 通知
- GitHub Actions 定时运行

## 快速开始（GitHub Actions）

1. Fork 本仓库。
2. 进入仓库 Settings → Secrets and variables → Actions，添加下方 secrets。
3. 进入 Actions，手动触发 `Rainyun Checkin` workflow（workflow_dispatch）。
4. 定时触发：默认 UTC 00:00（北京时间 08:00）。

## Secrets 列表

### 必填

- `RAINYUN_USER`：雨云账号用户名
- `RAINYUN_PWD`：雨云账号密码
- `TG_BOT_TOKEN`：Telegram Bot Token
- `TG_USER_ID`：Telegram Chat ID

### 可选

- `RAINYUN_API_KEY`：用于服务器到期检测与自动续费
- `RAINYUN_ACCOUNT_ID`：账号 ID（用于区分与 cookie 文件名）
- `RAINYUN_ACCOUNT_NAME`：账号备注名
- `AUTO_RENEW`：是否自动续费（true/false，默认 true）
- `RENEW_THRESHOLD_DAYS`：续费阈值天数（默认 7）
- `RENEW_PRODUCT_IDS`：续费白名单（逗号分隔的产品 ID）
- `TG_API_HOST`：Telegram API 代理
- `TG_PROXY_HOST` / `TG_PROXY_PORT` / `TG_PROXY_AUTH`：Telegram 代理设置

## 运行说明

- 定时触发使用 UTC 时间：`0 0 * * *` 即北京时间每天 08:00。
- 也可在 Actions 页面手动触发 workflow_dispatch。
- 当前 workflow 采用 **Docker 方式运行**：镜像由仓库内 Dockerfile 构建，单次运行后退出。

## 项目结构（简化）

```
rainyun/
├── scheduler/        # 定时任务（cron 执行/多账户运行器）
├── browser/          # Selenium 浏览器（登录/签到/验证码）
├── notify/           # Telegram 通知
├── server/           # 服务器管理与自动续费
├── data/             # 数据模型与存储（Account/Settings）
└── api/              # 雨云 API 客户端封装
```

## 常见问题

### 一键签到报 “Unable to obtain driver for chrome”
容器内已预装 chromium 与 chromium-driver。若仍报错，可检查 `CHROMEDRIVER_LOG_PATH` 日志输出。

### cookies 在哪里
每个账号独立保存：`data/cookies/cookies_<account_id>.json`

## 致谢

本项目基于以下仓库二次开发：

| 版本 | 作者 | 仓库 | 说明 |
|------|------|------|------|
| 原版 | SerendipityR | https://github.com/SerendipityR-2022/Rainyun-Qiandao | 初始 Python 版本 |
| 二改 | fatekey | https://github.com/fatekey/Rainyun-Qiandao | Docker 化改造 |
| 三改 | Jielumoon | 本仓库 | Web面板+多通知渠道+稳定性优化+自动续费 |
