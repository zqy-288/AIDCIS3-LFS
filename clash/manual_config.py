#!/usr/bin/env python3
"""
手动配置 Clash 的简化脚本
"""

import yaml
import os

def create_basic_config():
    """创建基础配置"""
    config = {
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
        
        'proxies': [
            {
                'name': 'example-server',
                'type': 'ss',
                'server': 'example.com',
                'port': 8388,
                'cipher': 'aes-256-gcm',
                'password': 'your-password'
            }
        ],
        
        'proxy-groups': [
            {
                'name': 'PROXY',
                'type': 'select',
                'proxies': ['example-server', 'DIRECT']
            },
            {
                'name': 'AUTO',
                'type': 'url-test',
                'proxies': ['example-server'],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300
            }
        ],
        
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
    
    return config

def main():
    print("=== Clash 手动配置助手 ===")
    print()
    
    # 获取用户输入
    print("请输入您的代理服务器信息：")
    
    proxy_type = input("代理类型 (ss/vmess/trojan): ").lower()
    server = input("服务器地址: ")
    port = input("端口: ")
    
    if proxy_type == 'ss':
        cipher = input("加密方式 (默认: aes-256-gcm): ") or 'aes-256-gcm'
        password = input("密码: ")
        
        proxy = {
            'name': 'my-proxy',
            'type': 'ss',
            'server': server,
            'port': int(port),
            'cipher': cipher,
            'password': password
        }
    
    elif proxy_type == 'vmess':
        uuid = input("UUID: ")
        alterId = input("alterId (默认: 0): ") or '0'
        cipher = input("加密方式 (默认: auto): ") or 'auto'
        
        proxy = {
            'name': 'my-proxy',
            'type': 'vmess',
            'server': server,
            'port': int(port),
            'uuid': uuid,
            'alterId': int(alterId),
            'cipher': cipher
        }
    
    elif proxy_type == 'trojan':
        password = input("密码: ")
        
        proxy = {
            'name': 'my-proxy',
            'type': 'trojan',
            'server': server,
            'port': int(port),
            'password': password
        }
    
    else:
        print("不支持的代理类型")
        return
    
    # 创建配置
    config = create_basic_config()
    config['proxies'] = [proxy]
    config['proxy-groups'][0]['proxies'] = ['my-proxy', 'DIRECT']
    config['proxy-groups'][1]['proxies'] = ['my-proxy']
    
    # 保存配置
    config_file = os.path.expanduser("~/.config/clash/config.yaml")
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"\n配置已保存到: {config_file}")
    print("现在可以运行 ./start_clash.sh 启动 Clash")

if __name__ == "__main__":
    main()
