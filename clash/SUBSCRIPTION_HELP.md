# 订阅配置帮助

## 关于您的订阅链接

您提供的订阅链接：
```
https://proxyinfo.net/api/v1/client/subscribe?token=756efe65e841768e21f042f3d0414153
```

**当前状态**: 无法直接访问（403 Forbidden）

这可能是由于以下原因：
1. 订阅链接需要特定的客户端或 User-Agent
2. 有 IP 地址限制
3. 需要在特定的网络环境中访问
4. 订阅服务暂时不可用

## 解决方案

### 方案一：在本地电脑获取配置

1. **在您的本地电脑上**（可以正常访问互联网的环境）：
   - 使用 Clash 客户端导入订阅链接
   - 导出配置文件或复制代理链接
   - 将配置传输到服务器

2. **传输方式**：
   ```bash
   # 方式1: 使用 scp 传输配置文件
   scp config.yaml user@server:~/.config/clash/
   
   # 方式2: 复制代理链接文本，然后在服务器上使用导入工具
   python3 import_config.py
   ```

### 方案二：手动配置

如果您知道具体的服务器信息，可以手动配置：

```bash
python3 manual_config.py
```

### 方案三：使用其他工具

1. **在本地使用 Clash 客户端**：
   - Windows: Clash for Windows
   - macOS: ClashX
   - 导入订阅后，复制配置内容

2. **使用在线转换工具**：
   - 将订阅链接转换为 Clash 配置
   - 复制生成的配置内容

## 配置示例

如果您有具体的服务器信息，可以参考以下格式：

### Shadowsocks 示例
```yaml
proxies:
  - name: "my-ss"
    type: ss
    server: example.com
    port: 8388
    cipher: aes-256-gcm
    password: your-password
```

### VMess 示例
```yaml
proxies:
  - name: "my-vmess"
    type: vmess
    server: example.com
    port: 443
    uuid: your-uuid
    alterId: 0
    cipher: auto
```

### Trojan 示例
```yaml
proxies:
  - name: "my-trojan"
    type: trojan
    server: example.com
    port: 443
    password: your-password
```

## 测试配置

配置完成后，可以这样测试：

```bash
# 启动 Clash
./start_clash.sh

# 设置代理
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

# 测试连接
curl -I https://www.google.com

# 测试 Gemini
gemini "Hello, can you introduce yourself?"
```

## 故障排除

### 1. 订阅链接无法访问
- 尝试在不同网络环境中访问
- 联系 VPN 服务提供商
- 使用官方客户端获取配置

### 2. 配置文件格式错误
```bash
# 验证配置文件语法
clash -t -d ~/.config/clash
```

### 3. 代理无法连接
- 检查服务器地址和端口
- 确认密码和加密方式正确
- 查看 Clash 日志：`tail -f ~/.config/clash/clash.log`

## 需要帮助？

如果您有以下信息，我可以帮您直接配置：

1. **服务器类型** (Shadowsocks/VMess/Trojan)
2. **服务器地址**
3. **端口号**
4. **密码/UUID**
5. **加密方式**（如果是 Shadowsocks）

或者，您可以：
1. 在本地电脑上成功导入订阅
2. 复制生成的代理链接或配置文件内容
3. 使用我们提供的导入工具导入到服务器
