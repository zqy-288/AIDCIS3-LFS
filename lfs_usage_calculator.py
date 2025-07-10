#!/usr/bin/env python3
"""
计算Git LFS使用量
"""

import subprocess
import re

def calculate_lfs_usage():
    """计算LFS文件总大小"""
    try:
        # 获取LFS文件列表和大小
        result = subprocess.run(['git', 'lfs', 'ls-files', '-s'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ 无法获取LFS文件信息")
            return
        
        lines = result.stdout.strip().split('\n')
        total_size = 0
        file_count = 0
        
        print("📊 Git LFS文件使用情况分析")
        print("=" * 60)
        
        for line in lines:
            if line.strip():
                # 解析文件大小
                match = re.search(r'\(([0-9.]+)\s*(KB|MB|GB)\)', line)
                if match:
                    size_str = match.group(1)
                    unit = match.group(2)
                    size = float(size_str)
                    
                    # 转换为字节
                    if unit == 'KB':
                        size_bytes = size * 1024
                    elif unit == 'MB':
                        size_bytes = size * 1024 * 1024
                    elif unit == 'GB':
                        size_bytes = size * 1024 * 1024 * 1024
                    else:
                        size_bytes = size
                    
                    total_size += size_bytes
                    file_count += 1
        
        # 转换为更易读的格式
        if total_size < 1024:
            size_display = f"{total_size:.1f} B"
        elif total_size < 1024 * 1024:
            size_display = f"{total_size / 1024:.1f} KB"
        elif total_size < 1024 * 1024 * 1024:
            size_display = f"{total_size / (1024 * 1024):.1f} MB"
        else:
            size_display = f"{total_size / (1024 * 1024 * 1024):.1f} GB"
        
        print(f"📁 LFS文件数量: {file_count}")
        print(f"💾 总使用空间: {size_display}")
        print(f"📈 GitHub免费配额: 1GB 存储 + 1GB/月 带宽")
        
        # 计算使用百分比
        usage_percent = (total_size / (1024 * 1024 * 1024)) * 100
        print(f"📊 存储配额使用率: {usage_percent:.1f}%")
        
        if usage_percent < 50:
            print("✅ 使用量正常，配额充足")
        elif usage_percent < 80:
            print("⚠️ 使用量较高，请注意监控")
        else:
            print("🚨 使用量接近限制，建议优化或升级")
        
        print("\n📋 文件类型分布:")
        file_types = {}
        for line in lines:
            if line.strip():
                # 提取文件扩展名
                if '*' in line:
                    filename = line.split('*')[1].strip()
                    ext = filename.split('.')[-1].lower() if '.' in filename else 'no_ext'
                    
                    match = re.search(r'\(([0-9.]+)\s*(KB|MB|GB)\)', line)
                    if match:
                        size_str = match.group(1)
                        unit = match.group(2)
                        size = float(size_str)
                        
                        if unit == 'MB':
                            size_mb = size
                        elif unit == 'KB':
                            size_mb = size / 1024
                        elif unit == 'GB':
                            size_mb = size * 1024
                        else:
                            size_mb = size / (1024 * 1024)
                        
                        if ext not in file_types:
                            file_types[ext] = {'count': 0, 'size': 0}
                        file_types[ext]['count'] += 1
                        file_types[ext]['size'] += size_mb
        
        for ext, info in sorted(file_types.items(), key=lambda x: x[1]['size'], reverse=True):
            print(f"  .{ext}: {info['count']} 文件, {info['size']:.1f} MB")
        
        print("\n🔗 查看详细使用情况:")
        print("1. GitHub仓库 > Settings > Git LFS")
        print("2. 或访问: https://github.com/zqy-288/AIDCIS3-LFS/settings/lfs")
        
    except Exception as e:
        print(f"❌ 计算失败: {e}")

if __name__ == "__main__":
    calculate_lfs_usage()
