#!/usr/bin/env python3
"""
检查图像文件脚本
"""

import os
import sys
from pathlib import Path

def check_image_files():
    """检查图像文件是否存在"""
    print("📂 检查面板B图像文件")
    print("=" * 60)
    
    base_dir = os.getcwd()
    print(f"当前目录: {base_dir}")
    print()
    
    # 检查H00001图像
    h00001_path = os.path.join(base_dir, "Data/H00001/BISDM/result")
    print(f"🔍 检查H00001图像路径:")
    print(f"  路径: {h00001_path}")
    
    if os.path.exists(h00001_path):
        print(f"  ✅ 目录存在")
        try:
            files = os.listdir(h00001_path)
            png_files = [f for f in files if f.lower().endswith('.png')]
            jpg_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg'))]
            
            print(f"  📊 文件统计:")
            print(f"    PNG文件: {len(png_files)} 个")
            print(f"    JPG文件: {len(jpg_files)} 个")
            print(f"    总文件: {len(files)} 个")
            
            if png_files:
                print(f"  📋 PNG文件列表:")
                for i, f in enumerate(png_files[:5]):
                    full_path = os.path.join(h00001_path, f)
                    size = os.path.getsize(full_path)
                    print(f"    {i+1}. {f} ({size} bytes)")
                if len(png_files) > 5:
                    print(f"    ... 还有 {len(png_files)-5} 个文件")
            else:
                print(f"  ❌ 没有找到PNG文件")
                
        except Exception as e:
            print(f"  ❌ 读取目录失败: {e}")
    else:
        print(f"  ❌ 目录不存在")
    
    print()
    
    # 检查H00002图像
    h00002_path = os.path.join(base_dir, "Data/H00002/BISDM/result")
    print(f"🔍 检查H00002图像路径:")
    print(f"  路径: {h00002_path}")
    
    if os.path.exists(h00002_path):
        print(f"  ✅ 目录存在")
        try:
            files = os.listdir(h00002_path)
            png_files = [f for f in files if f.lower().endswith('.png')]
            jpg_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg'))]
            
            print(f"  📊 文件统计:")
            print(f"    PNG文件: {len(png_files)} 个")
            print(f"    JPG文件: {len(jpg_files)} 个")
            print(f"    总文件: {len(files)} 个")
            
            if png_files:
                print(f"  📋 PNG文件列表:")
                for i, f in enumerate(png_files[:5]):
                    full_path = os.path.join(h00002_path, f)
                    size = os.path.getsize(full_path)
                    print(f"    {i+1}. {f} ({size} bytes)")
                if len(png_files) > 5:
                    print(f"    ... 还有 {len(png_files)-5} 个文件")
            else:
                print(f"  ❌ 没有找到PNG文件")
                
        except Exception as e:
            print(f"  ❌ 读取目录失败: {e}")
    else:
        print(f"  ❌ 目录不存在")
    
    print()
    print("🔧 **解决方案**:")
    print("=" * 60)
    
    # 检查是否有图像文件
    h00001_has_images = os.path.exists(h00001_path) and any(f.lower().endswith('.png') for f in os.listdir(h00001_path) if os.path.isfile(os.path.join(h00001_path, f)))
    h00002_has_images = os.path.exists(h00002_path) and any(f.lower().endswith('.png') for f in os.listdir(h00002_path) if os.path.isfile(os.path.join(h00002_path, f)))
    
    if not h00001_has_images and not h00002_has_images:
        print("❌ 两个孔位都没有图像文件")
        print()
        print("需要添加测试图像文件:")
        print("1. 创建目录结构:")
        print(f"   mkdir -p '{h00001_path}'")
        print(f"   mkdir -p '{h00002_path}'")
        print()
        print("2. 添加PNG图像文件到这些目录")
        print("   (可以是任何PNG格式的图像文件)")
        
    elif not h00001_has_images:
        print("❌ H00001没有图像文件")
        print(f"请添加PNG图像文件到: {h00001_path}")
        
    elif not h00002_has_images:
        print("❌ H00002没有图像文件")
        print(f"请添加PNG图像文件到: {h00002_path}")
        
    else:
        print("✅ 图像文件检查正常")
        print("问题可能在于:")
        print("1. 图像加载逻辑")
        print("2. 图像显示组件")
        print("3. 数据同步问题")

def main():
    print("🖼️ 面板B图像文件检查工具")
    print("=" * 80)
    
    check_image_files()
    
    print()
    print("🧪 **下一步测试**:")
    print("=" * 60)
    
    print("如果图像文件存在:")
    print("1. 重新启动程序")
    print("2. 选择孔位H00001")
    print("3. 观察控制台是否输出:")
    print("   '✅ 为孔位 H00001 加载了 X 张内窥镜图片'")
    print("4. 点击'启动算法'")
    print("5. 观察是否输出:")
    print("   '🔍 调试: 尝试显示图像索引 0'")
    print()
    
    print("如果图像文件不存在:")
    print("1. 按照上述解决方案创建目录和添加文件")
    print("2. 重新测试")

if __name__ == "__main__":
    main()
