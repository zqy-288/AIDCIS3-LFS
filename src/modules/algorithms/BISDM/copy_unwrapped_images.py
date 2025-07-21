#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path

def copy_with_offset(source_dir, target_dir, offset=50):
    """
    将source_dir中的unwrapped图像复制到target_dir，并给文件名加上偏移量
    
    Args:
        source_dir: 源目录路径
        target_dir: 目标目录路径
        offset: 文件名偏移量
    """
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 获取源目录中的所有png文件
    source_files = sorted([f for f in os.listdir(source_dir) if f.endswith('.png')])
    
    print(f"找到{len(source_files)}个图像文件")
    
    # 复制并重命名文件
    for source_file in source_files:
        # 解析文件名和编号
        parts = source_file.split('_')
        prefix = parts[0]
        number_str = parts[1].split('.')[0]  # 获取数字部分
        number = int(number_str)
        
        # 创建新的文件名
        new_number = number + offset
        new_number_str = f"{new_number:04d}"  # 保持4位数格式
        new_filename = f"{prefix}_{new_number_str}.png"
        
        # 源文件和目标文件的完整路径
        source_path = os.path.join(source_dir, source_file)
        target_path = os.path.join(target_dir, new_filename)
        
        # 复制文件
        shutil.copy2(source_path, target_path)
        print(f"已复制: {source_file} -> {new_filename}")

if __name__ == "__main__":
    # 设置源目录和目标目录
    script_dir = Path(__file__).parent.absolute()
    source_dir = os.path.join(script_dir, "output_final", "02_unwrapped")
    target_dir = os.path.join(script_dir, "data")
    
    # 执行复制
    copy_with_offset(source_dir, target_dir, offset=50)
    print("处理完成！") 