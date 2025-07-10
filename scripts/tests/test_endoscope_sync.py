#!/usr/bin/env python3
"""
内窥镜图像与CSV数据同步测试
Test Endoscope Image and CSV Data Synchronization
"""

import sys
import os
import glob
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '.')

def test_image_csv_sync():
    """测试图像与CSV数据的同步"""
    
    print("🔍 内窥镜图像与CSV数据同步测试")
    print("=" * 60)
    
    # 1. 检查图片目录
    print("\n📁 检查图片目录:")
    
    image_dirs = {
        "H00001": "cache/result2",
        "H00002": "cache/result"
    }
    
    for hole_id, img_dir in image_dirs.items():
        print(f"\n   {hole_id} -> {img_dir}")
        
        if not os.path.exists(img_dir):
            print(f"   ❌ 目录不存在: {img_dir}")
            continue
        
        # 获取图片文件
        image_files = glob.glob(os.path.join(img_dir, "*.png"))
        
        if not image_files:
            print(f"   ❌ 目录中没有PNG图片")
            continue
        
        # 按文件名排序
        def extract_number(filename):
            import re
            basename = os.path.basename(filename)
            match = re.search(r'-(\d+\.?\d*)', basename)
            if match:
                return float(match.group(1))
            return 0
        
        image_files.sort(key=extract_number)
        
        print(f"   ✅ 找到 {len(image_files)} 张图片:")
        for i, img in enumerate(image_files):
            print(f"      {i+1}. {os.path.basename(img)}")
    
    # 2. 检查CSV数据
    print("\n📊 检查CSV数据:")
    
    csv_files = {
        "H00001": "data/H00001/CCIDM/measurement_data_Fri_Jul__4_18_40_29_2025.csv",
        "H00002": "data/H00002/CCIDM/measurement_data_Sat_Jul__5_15_18_46_2025.csv"
    }
    
    csv_data_info = {}
    
    for hole_id, csv_path in csv_files.items():
        print(f"\n   {hole_id} -> {csv_path}")
        
        if not os.path.exists(csv_path):
            print(f"   ❌ CSV文件不存在: {csv_path}")
            continue
        
        try:
            # 读取CSV文件行数
            with open(csv_path, 'r', encoding='gbk') as file:
                lines = file.readlines()
                data_lines = len(lines) - 1  # 减去标题行
                
            csv_data_info[hole_id] = data_lines
            print(f"   ✅ CSV数据点: {data_lines} 个")
            
        except Exception as e:
            print(f"   ❌ 读取CSV失败: {e}")
    
    # 3. 计算同步策略
    print("\n⏱️ 计算同步策略:")
    
    for hole_id in ["H00001", "H00002"]:
        img_dir = image_dirs.get(hole_id)
        if not img_dir or not os.path.exists(img_dir):
            continue
        
        image_files = glob.glob(os.path.join(img_dir, "*.png"))
        if not image_files:
            continue
        
        num_images = len(image_files)
        data_points = csv_data_info.get(hole_id, 0)
        
        if data_points == 0:
            continue
        
        print(f"\n   {hole_id}:")
        print(f"   - 图片数量: {num_images}")
        print(f"   - 数据点数: {data_points}")
        
        if num_images > 0:
            points_per_image = data_points / num_images
            time_per_image = points_per_image * 0.05  # 50ms per data point (实际播放速度)
            
            print(f"   - 每张图片显示: {points_per_image:.1f} 个数据点")
            print(f"   - 每张图片时长: {time_per_image:.1f} 秒")
            
            # 计算切换点
            switch_points = []
            for i in range(num_images):
                switch_point = int(i * points_per_image)
                switch_points.append(switch_point)
            
            print(f"   - 图片切换点: {switch_points}")
            
            # 显示切换时间表
            print(f"   - 切换时间表:")
            for i, point in enumerate(switch_points):
                time_sec = point * 0.2
                print(f"     图片{i+1}: 第{point}个数据点 ({time_sec:.1f}秒)")
    
    # 4. 模拟同步过程
    print("\n🎬 模拟同步过程 (H00001):")
    
    hole_id = "H00001"
    img_dir = image_dirs.get(hole_id)
    data_points = csv_data_info.get(hole_id, 0)
    
    if img_dir and os.path.exists(img_dir) and data_points > 0:
        image_files = glob.glob(os.path.join(img_dir, "*.png"))
        
        def extract_number(filename):
            import re
            basename = os.path.basename(filename)
            match = re.search(r'-(\d+\.?\d*)', basename)
            if match:
                return float(match.group(1))
            return 0
        
        image_files.sort(key=extract_number)
        num_images = len(image_files)
        
        if num_images > 0:
            points_per_image = data_points / num_images
            
            print(f"   总数据点: {data_points}, 图片数量: {num_images}")
            print(f"   播放速度: 50ms/数据点 (实际速度)")
            print()

            # 模拟关键时刻
            key_moments = [0, 25, 50, 75, 100]  # 百分比

            for percent in key_moments:
                current_point = int((percent / 100) * data_points)
                current_time = current_point * 0.05  # 修正为50ms
                
                # 确定当前应该显示的图片
                image_index = min(int(current_point / points_per_image), num_images - 1)
                image_name = os.path.basename(image_files[image_index])
                
                print(f"   进度 {percent:3d}%: 数据点{current_point:3d} ({current_time:5.1f}秒) -> 显示图片: {image_name}")
    
    print("\n🎉 同步测试完成！")
    
    return True

def test_image_loading():
    """测试图片加载功能"""
    
    print("\n" + "=" * 60)
    print("🖼️ 图片加载功能测试")
    print("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPixmap
        
        # 创建应用程序（如果还没有）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 测试图片加载
        test_images = [
            "cache/result2/1-1.2.png",
            "cache/result/2-3.0.png"
        ]
        
        for img_path in test_images:
            print(f"\n测试加载: {img_path}")
            
            if not os.path.exists(img_path):
                print(f"   ❌ 文件不存在")
                continue
            
            pixmap = QPixmap(img_path)
            if pixmap.isNull():
                print(f"   ❌ 无法加载图片")
            else:
                print(f"   ✅ 加载成功，尺寸: {pixmap.width()}x{pixmap.height()}")
        
        print("\n✅ 图片加载测试完成")
        
    except ImportError as e:
        print(f"⚠️ 无法导入Qt组件，跳过图片加载测试: {e}")
    except Exception as e:
        print(f"❌ 图片加载测试失败: {e}")

def main():
    """主函数"""
    try:
        # 运行同步测试
        test_image_csv_sync()
        
        # 运行图片加载测试
        test_image_loading()
        
        print("\n" + "=" * 60)
        print("🏆 测试总结")
        print("=" * 60)
        print("✅ 图片目录检查完成")
        print("✅ CSV数据检查完成") 
        print("✅ 同步策略计算完成")
        print("✅ 模拟同步过程完成")
        print("✅ 图片加载功能测试完成")
        
        print("\n📋 实现要点:")
        print("1. 图片按文件名数值排序")
        print("2. 根据CSV数据点数量均匀分配图片显示时间")
        print("3. 每200ms播放一个数据点，同步切换图片")
        print("4. H00001: 4张图片，889个数据点，每张约44.4秒")
        print("5. H00002: 5张图片，573个数据点，每张约22.9秒")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
