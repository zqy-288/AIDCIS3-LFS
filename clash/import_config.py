#!/usr/bin/env python3
"""
从文件或文本导入 Clash 配置
"""

import yaml
import os
import sys
import base64
import json
from urllib.parse import urlparse

def parse_vmess_url(vmess_url):
    """解析 VMess URL"""
    try:
        vmess_data = vmess_url.replace('vmess://', '')
        decoded = base64.b64decode(vmess_data).decode('utf-8')
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

def parse_ss_url(ss_url):
    """解析 Shadowsocks URL"""
    try:
        parsed = urlparse(ss_url)
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

def parse_trojan_url(trojan_url):
    """解析 Trojan URL"""
    try:
        parsed = urlparse(trojan_url)
        
        return {
            'name': parsed.fragment or 'trojan-server',
            'type': 'trojan',
            'server': parsed.hostname,
            'port': parsed.port or 443,
            'password': parsed.username
        }
    except Exception as e:
        print(f"解析 Trojan 失败: {e}")
        return None

def create_base_config():
    """创建基础配置"""
    return {
        'port': 7890,
        'socks-port': 7891,
        'allow-lan': True,
        'bind-address': '*',
        'mode': 'rule',
        'log-level': 'info',
        'external-controller': '127.0.0.1:9090',
        'external-ui': 'dashboard',
        
        'dns': {
            'enable': True,
            'listen': '0.0.0.0:53',
            'default-nameserver': ['223.5.5.5', '8.8.8.8'],
            'enhanced-mode': 'fake-ip',
            'fake-ip-range': '198.18.0.1/16',
            'nameserver': ['223.5.5.5', '8.8.8.8', '1.1.1.1']
        },
        
        'rules': [
            'GEOIP,CN,DIRECT',
            'DOMAIN-SUFFIX,google.com,PROXY',
            'DOMAIN-SUFFIX,googleapis.com,PROXY',
            'DOMAIN-SUFFIX,googleusercontent.com,PROXY',
            'DOMAIN-SUFFIX,gstatic.com,PROXY',
            'DOMAIN-SUFFIX,github.com,PROXY',
            'DOMAIN-SUFFIX,githubusercontent.com,PROXY',
            'DOMAIN-SUFFIX,openai.com,PROXY',
            'DOMAIN-SUFFIX,anthropic.com,PROXY',
            'IP-CIDR,192.168.0.0/16,DIRECT',
            'IP-CIDR,10.0.0.0/8,DIRECT',
            'IP-CIDR,172.16.0.0/12,DIRECT',
            'IP-CIDR,127.0.0.0/8,DIRECT',
            'MATCH,DIRECT'
        ]
    }

def import_from_text(text):
    """从文本导入配置"""
    proxies = []
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('vmess://'):
            proxy = parse_vmess_url(line)
            if proxy:
                proxies.append(proxy)
        elif line.startswith('ss://'):
            proxy = parse_ss_url(line)
            if proxy:
                proxies.append(proxy)
        elif line.startswith('trojan://'):
            proxy = parse_trojan_url(line)
            if proxy:
                proxies.append(proxy)
    
    return proxies

def main():
    print("=== Clash 配置导入工具 ===")
    print()
    print("选择导入方式:")
    print("1. 从文件导入")
    print("2. 手动输入代理链接")
    print("3. 输入单个服务器配置")
    
    choice = input("请选择 (1-3): ")
    
    proxies = []
    
    if choice == '1':
        filename = input("请输入文件路径: ")
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            proxies = import_from_text(content)
        else:
            print("文件不存在")
            return
    
    elif choice == '2':
        print("请输入代理链接 (每行一个，输入空行结束):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        
        text = '\n'.join(lines)
        proxies = import_from_text(text)
    
    elif choice == '3':
        print("请运行 python3 manual_config.py 进行手动配置")
        return
    
    else:
        print("无效选择")
        return
    
    if not proxies:
        print("没有找到有效的代理配置")
        return
    
    print(f"找到 {len(proxies)} 个代理服务器")
    
    # 创建配置
    config = create_base_config()
    config['proxies'] = proxies
    
    # 创建代理组
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
    config_file = os.path.expanduser("~/.config/clash/config.yaml")
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"配置已保存到: {config_file}")
    print("现在可以运行 ./start_clash.sh 启动 Clash")

if __name__ == "__main__":
    main()
