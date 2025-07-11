#!/usr/bin/env python3
"""
Clash 代理切换脚本
"""

import requests
import json
import sys

def get_proxies():
    """获取所有代理列表"""
    try:
        response = requests.get("http://127.0.0.1:9090/proxies")
        return response.json()
    except Exception as e:
        print(f"获取代理列表失败: {e}")
        return None

def switch_proxy(group_name, proxy_name):
    """切换代理"""
    try:
        data = {"name": proxy_name}
        response = requests.put(
            f"http://127.0.0.1:9090/proxies/{group_name}",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 204:
            print(f"成功切换到: {proxy_name}")
            return True
        else:
            print(f"切换失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"切换代理失败: {e}")
        return False

def list_servers_by_region(region):
    """列出指定地区的服务器"""
    proxies_data = get_proxies()
    if not proxies_data:
        return []
    
    servers = []
    for name, info in proxies_data["proxies"].items():
        if region.lower() in name.lower():
            servers.append(name)
    
    return servers

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 switch_proxy.py list [region]  # 列出服务器")
        print("  python3 switch_proxy.py sg             # 切换到新加坡")
        print("  python3 switch_proxy.py jp             # 切换到日本")
        print("  python3 switch_proxy.py kr             # 切换到韩国")
        print("  python3 switch_proxy.py us             # 切换到美国")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        region = sys.argv[2] if len(sys.argv) > 2 else ""
        proxies_data = get_proxies()
        if proxies_data:
            print("可用的代理服务器:")
            for name in proxies_data["proxies"].keys():
                if region.lower() in name.lower() or not region:
                    print(f"  {name}")
    
    elif command in ["sg", "singapore", "新加坡"]:
        servers = list_servers_by_region("新加坡")
        if servers:
            # 选择第一个新加坡服务器
            server = servers[0]
            print(f"切换到新加坡服务器: {server}")
            switch_proxy("性价比机场", server)
        else:
            print("没有找到新加坡服务器")
    
    elif command in ["jp", "japan", "日本"]:
        servers = list_servers_by_region("日本")
        if servers:
            # 选择第一个日本服务器
            server = servers[0]
            print(f"切换到日本服务器: {server}")
            switch_proxy("性价比机场", server)
        else:
            print("没有找到日本服务器")
    
    elif command in ["kr", "korea", "韩国"]:
        servers = list_servers_by_region("韩国")
        if servers:
            server = servers[0]
            print(f"切换到韩国服务器: {server}")
            switch_proxy("性价比机场", server)
        else:
            print("没有找到韩国服务器")
    
    elif command in ["us", "usa", "美国"]:
        servers = list_servers_by_region("美国")
        if servers:
            server = servers[0]
            print(f"切换到美国服务器: {server}")
            switch_proxy("性价比机场", server)
        else:
            print("没有找到美国服务器")
    
    else:
        print(f"未知命令: {command}")

if __name__ == "__main__":
    main()
