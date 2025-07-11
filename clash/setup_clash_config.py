#!/usr/bin/env python3
"""
Clash 配置助手
帮助用户快速配置 Clash
"""

import os
import yaml
import sys

def setup_shadowsocks():
    """配置 Shadowsocks"""
    print("=== Shadowsocks 配置 ===")
    server = input("服务器地址: ")
    port = input("端口: ")
    password = input("密码: ")
    cipher = input("加密方式 (默认: aes-256-gcm): ") or "aes-256-gcm"
    
    return {
        "name": "ss-proxy",
        "type": "ss",
        "server": server,
        "port": int(port),
        "cipher": cipher,
        "password": password
    }

def setup_vmess():
    """配置 VMess"""
    print("=== VMess 配置 ===")
    server = input("服务器地址: ")
    port = input("端口: ")
    uuid = input("UUID: ")
    alterId = input("alterId (默认: 0): ") or "0"
    cipher = input("加密方式 (默认: auto): ") or "auto"
    
    return {
        "name": "vmess-proxy",
        "type": "vmess",
        "server": server,
        "port": int(port),
        "uuid": uuid,
        "alterId": int(alterId),
        "cipher": cipher
    }

def setup_trojan():
    """配置 Trojan"""
    print("=== Trojan 配置 ===")
    server = input("服务器地址: ")
    port = input("端口: ")
    password = input("密码: ")
    
    return {
        "name": "trojan-proxy",
        "type": "trojan",
        "server": server,
        "port": int(port),
        "password": password
    }

def main():
    config_dir = os.path.expanduser("~/.config/clash")
    config_file = os.path.join(config_dir, "config.yaml")
    
    print("Clash 配置助手")
    print("=" * 30)
    
    # 选择代理类型
    print("请选择您的代理类型:")
    print("1. Shadowsocks")
    print("2. VMess")
    print("3. Trojan")
    print("4. 从订阅链接导入")
    
    choice = input("请输入选择 (1-4): ")
    
    proxy_config = None
    
    if choice == "1":
        proxy_config = setup_shadowsocks()
    elif choice == "2":
        proxy_config = setup_vmess()
    elif choice == "3":
        proxy_config = setup_trojan()
    elif choice == "4":
        url = input("请输入订阅链接: ")
        print("订阅链接功能需要额外实现，请手动配置")
        return
    else:
        print("无效选择")
        return
    
    # 读取现有配置
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    else:
        print("配置文件不存在")
        return
    
    # 更新代理配置
    config['proxies'] = [proxy_config]
    config['proxy-groups'][0]['proxies'] = [proxy_config['name'], 'DIRECT']
    config['proxy-groups'][1]['proxies'] = [proxy_config['name']]
    
    # 保存配置
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"配置已保存到: {config_file}")
    print("现在可以运行 ./start_clash.sh 启动 Clash")

if __name__ == "__main__":
    main()
