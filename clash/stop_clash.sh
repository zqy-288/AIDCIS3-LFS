#!/bin/bash

# Clash 停止脚本

CONFIG_DIR="$HOME/.config/clash"
PID_FILE="$CONFIG_DIR/clash.pid"

# 检查 PID 文件是否存在
if [ ! -f "$PID_FILE" ]; then
    echo "Clash 没有在运行或 PID 文件不存在"
    exit 0
fi

# 读取 PID
PID=$(cat "$PID_FILE")

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    echo "Clash 进程不存在，清理 PID 文件"
    rm -f "$PID_FILE"
    exit 0
fi

# 停止进程
echo "停止 Clash (PID: $PID)..."
kill $PID

# 等待进程结束
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "Clash 已停止"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# 如果进程仍然存在，强制杀死
echo "强制停止 Clash..."
kill -9 $PID
rm -f "$PID_FILE"
echo "Clash 已强制停止"
