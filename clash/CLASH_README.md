# Clash 安装和使用指南

## 安装完成

✅ Clash Meta (mihomo) v1.18.5 已成功安装
✅ 配置文件模板已创建
✅ 启动和停止脚本已准备就绪

## 文件说明

- `/usr/local/bin/clash` - Clash 可执行文件
- `~/.config/clash/config.yaml` - 配置文件
- `start_clash.sh` - 启动脚本
- `stop_clash.sh` - 停止脚本
- `setup_clash_config.py` - 配置助手

## 使用步骤

### 1. 配置您的 VPN 信息

#### 方法一：从订阅链接更新（如果可用）
```bash
python3 update_subscription.py "your-subscription-url"
```

#### 方法二：导入代理链接
```bash
python3 import_config.py
```

#### 方法三：手动配置单个服务器
```bash
python3 manual_config.py
```

#### 方法四：手动编辑配置文件
```bash
nano ~/.config/clash/config.yaml
```

在 `proxies` 部分替换您的 VPN 配置信息：

**Shadowsocks 示例：**
```yaml
proxies:
  - name: "my-ss"
    type: ss
    server: your-server.com
    port: 8388
    cipher: aes-256-gcm
    password: your-password
```

**VMess 示例：**
```yaml
proxies:
  - name: "my-vmess"
    type: vmess
    server: your-server.com
    port: 443
    uuid: your-uuid
    alterId: 0
    cipher: auto
```

**Trojan 示例：**
```yaml
proxies:
  - name: "my-trojan"
    type: trojan
    server: your-server.com
    port: 443
    password: your-password
```

### 2. 启动 Clash

```bash
./start_clash.sh
```

### 3. 配置系统代理

启动成功后，Clash 会在以下端口提供服务：
- HTTP 代理: `http://127.0.0.1:7890`
- SOCKS5 代理: `socks5://127.0.0.1:7891`
- Web 控制台: `http://127.0.0.1:9090/ui`

#### 设置环境变量（临时）
```bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
```

#### 设置环境变量（永久）
```bash
echo 'export http_proxy=http://127.0.0.1:7890' >> ~/.bashrc
echo 'export https_proxy=http://127.0.0.1:7890' >> ~/.bashrc
source ~/.bashrc
```

### 4. 测试连接

```bash
# 测试 Google 连接
curl -I https://www.google.com

# 测试 Gemini API
gemini "Hello, can you introduce yourself?"
```

### 5. 停止 Clash

```bash
./stop_clash.sh
```

## 常用命令

```bash
# 查看 Clash 状态
ps aux | grep clash

# 查看 Clash 日志
tail -f ~/.config/clash/clash.log

# 重启 Clash
./stop_clash.sh && ./start_clash.sh

# 测试代理连接
curl --proxy http://127.0.0.1:7890 https://www.google.com
```

## 故障排除

### 1. 启动失败
- 检查配置文件语法：`clash -t -d ~/.config/clash`
- 查看日志文件：`cat ~/.config/clash/clash.log`

### 2. 无法连接
- 确认 VPN 服务器信息正确
- 检查防火墙设置
- 尝试不同的代理协议

### 3. 端口冲突
- 修改配置文件中的端口号
- 检查端口占用：`netstat -tlnp | grep 7890`

## 高级配置

### 自定义规则
编辑 `~/.config/clash/config.yaml` 中的 `rules` 部分来自定义路由规则。

### Web 控制台
访问 `http://127.0.0.1:9090/ui` 来使用图形界面管理 Clash。

### 订阅更新
如果您有订阅链接，可以定期更新配置：
```bash
wget -O ~/.config/clash/config.yaml "your-subscription-url"
```

## 注意事项

1. 请确保您的 VPN 服务合法合规
2. 仅用于学术和开发目的
3. 定期更新 Clash 版本以获得最新功能和安全修复
4. 保护好您的配置文件，避免泄露敏感信息
