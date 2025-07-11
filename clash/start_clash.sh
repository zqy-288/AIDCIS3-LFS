#!/bin/bash

# Clash 启动脚本

CONFIG_DIR="$HOME/.config/clash"
CONFIG_FILE="$CONFIG_DIR/config.yaml"
PID_FILE="$CONFIG_DIR/clash.pid"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 配置文件不存在: $CONFIG_FILE"
    echo "请先配置您的 VPN 信息"
    exit 1
fi

# 检查是否已经在运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Clash 已经在运行 (PID: $PID)"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# 启动 Clash
echo "启动 Clash..."
nohup clash -d "$CONFIG_DIR" > "$CONFIG_DIR/clash.log" 2>&1 &
PID=$!

# 保存 PID
echo $PID > "$PID_FILE"

echo "Clash 已启动 (PID: $PID)"
echo "HTTP 代理: http://127.0.0.1:7890"
echo "SOCKS5 代理: socks5://127.0.0.1:7891"
echo "Web 控制台: http://127.0.0.1:9090/ui"
echo "日志文件: $CONFIG_DIR/clash.log"

# 等待几秒钟检查是否启动成功
sleep 3
if ps -p $PID > /dev/null 2>&1; then
    echo "Clash 启动成功!"
else
    echo "Clash 启动失败，请检查日志文件"
    rm -f "$PID_FILE"
    exit 1
fi
