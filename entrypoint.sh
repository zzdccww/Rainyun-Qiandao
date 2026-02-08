#!/bin/sh
# 雨云自动签到启动脚本
# 支持定时模式或单次执行
set -e

if [ "$CRON_MODE" = "true" ]; then
    echo "=== 定时模式启用 ==="
    /usr/local/bin/python -u -m rainyun.scheduler.cron_sync || echo "警告: cron 同步失败"
    echo "=== cron 守护进程启动 ==="
    exec /usr/sbin/cron -f
fi

echo "=== 单次执行 ==="
exec /usr/local/bin/python -u -m rainyun.scheduler.cron_runner
