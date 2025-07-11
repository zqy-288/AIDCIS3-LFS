#!/usr/bin/env python3
"""
Clash 订阅更新脚本
"""

import requests
import base64
import yaml
import os
import sys
from urllib.parse import urlparse, parse_qs

def decode_subscription(content):
    """解码订阅内容"""
    try:
        # 尝试 base64 解码
        decoded = base64.b64decode(content).decode('utf-8')
        return decoded
    except:
        # 如果不是 base64，直接返回
        return content

def parse_vmess(vmess_url):
    """解析 VMess URL"""
    try:
        # 移除 vmess:// 前缀
        vmess_data = vmess_url.replace('vmess://', '')
        # Base64 解码
        decoded = base64.b64decode(vmess_data).decode('utf-8')
        import json
        config = json.loads(decoded)
        
        return {
            'name': config.get('ps', 'vmess-server'),
            'type': 'vmess',
            'server': config.get('add'),
            'port': int(config.get('port', 443)),
            'uuid': config.get('id'),
            'alterId': int(config.get('aid', 0)),
            'cipher': config.get('scy', 'auto'),
            'network': config.get('net', 'tcp'),
            'tls': config.get('tls') == 'tls'
        }
    except Exception as e:
        print(f"解析 VMess 失败: {e}")
        return None

def parse_ss(ss_url):
    """解析 Shadowsocks URL"""
    try:
        # 解析 ss:// URL
        parsed = urlparse(ss_url)
        
        # 解码用户信息
        userinfo = base64.b64decode(parsed.username).decode('utf-8')
        method, password = userinfo.split(':', 1)
        
        return {
            'name': parsed.fragment or 'ss-server',
            'type': 'ss',
            'server': parsed.hostname,
            'port': parsed.port,
            'cipher': method,
            'password': password
        }
    except Exception as e:
        print(f"解析 Shadowsocks 失败: {e}")
        return None

def download_subscription(url):
    """下载订阅"""
    headers = {
        'User-Agent': 'clash'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"下载订阅失败: {e}")
        return None

def update_clash_config(subscription_url):
    """更新 Clash 配置"""
    print(f"正在下载订阅: {subscription_url}")
    
    # 下载订阅
    content = download_subscription(subscription_url)
    if not content:
        return False
    
    # 检查是否是 HTML 错误页面
    if content.strip().startswith('<!DOCTYPE html>') or content.strip().startswith('<html'):
        print("错误: 下载的内容是 HTML 页面，可能是访问被拒绝或订阅链接失效")
        return False
    
    # 解码订阅内容
    decoded_content = decode_subscription(content)
    
    # 解析代理服务器
    proxies = []
    lines = decoded_content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('vmess://'):
            proxy = parse_vmess(line)
            if proxy:
                proxies.append(proxy)
        elif line.startswith('ss://'):
            proxy = parse_ss(line)
            if proxy:
                proxies.append(proxy)
        # 可以添加更多协议支持
    
    if not proxies:
        print("错误: 没有找到有效的代理服务器")
        return False
    
    print(f"找到 {len(proxies)} 个代理服务器")
    
    # 读取基础配置模板
    config_file = os.path.expanduser("~/.config/clash/config.yaml")
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    else:
        print("错误: 配置文件不存在")
        return False
    
    # 更新代理列表
    config['proxies'] = proxies
    
    # 更新代理组
    proxy_names = [p['name'] for p in proxies]
    config['proxy-groups'] = [
        {
            'name': 'PROXY',
            'type': 'select',
            'proxies': proxy_names + ['DIRECT']
        },
        {
            'name': 'AUTO',
            'type': 'url-test',
            'proxies': proxy_names,
            'url': 'http://www.gstatic.com/generate_204',
            'interval': 300
        }
    ]
    
    # 保存配置
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"配置已更新: {config_file}")
    return True

def main():
    if len(sys.argv) != 2:
        print("用法: python3 update_subscription.py <订阅链接>")
        sys.exit(1)
    
    subscription_url = sys.argv[1]
    
    if update_clash_config(subscription_url):
        print("订阅更新成功！")
        print("现在可以运行 ./start_clash.sh 启动 Clash")
    else:
        print("订阅更新失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
