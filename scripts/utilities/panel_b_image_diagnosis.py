#!/usr/bin/env python3
"""
面板B图像显示问题诊断脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def check_image_files():
    """检查图像文件是否存在"""
    print("📂 检查图像文件...")
    
    base_dir = os.getcwd()
    image_paths = {
        "H00001": os.path.join(base_dir, "Data/H00001/BISDM/result"),
        "H00002": os.path.join(base_dir, "Data/H00002/BISDM/result")
    }
    
    results = {}
    
    for hole_id, path in image_paths.items():
        print(f"\n🔍 检查 {hole_id}:")
        print(f"  路径: {path}")
        
        if os.path.exists(path):
            print(f"  ✅ 目录存在")
            try:
                files = os.listdir(path)
                png_files = [f for f in files if f.lower().endswith('.png')]
                jpg_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg'))]
                
                print(f"  📊 文件统计:")
                print(f"    PNG文件: {len(png_files)} 个")
                print(f"    JPG文件: {len(jpg_files)} 个")
                print(f"    总文件: {len(files)} 个")
                
                if png_files:
                    print(f"  📋 PNG文件列表:")
                    for i, f in enumerate(png_files[:5]):  # 只显示前5个
                        print(f"    {i+1}. {f}")
                    if len(png_files) > 5:
                        print(f"    ... 还有 {len(png_files)-5} 个文件")
                
                results[hole_id] = {
                    "exists": True,
                    "png_count": len(png_files),
                    "jpg_count": len(jpg_files),
                    "files": png_files[:3]  # 保存前3个文件名用于测试
                }
                
            except Exception as e:
                print(f"  ❌ 读取目录失败: {e}")
                results[hole_id] = {"exists": True, "error": str(e)}
        else:
            print(f"  ❌ 目录不存在")
            results[hole_id] = {"exists": False}
    
    return results

def check_endoscope_view():
    """检查内窥镜视图组件"""
    print("\n🔧 检查内窥镜视图组件...")
    
    try:
        # 检查endoscope_view.py文件
        if os.path.exists("modules/endoscope_view.py"):
            print("✅ endoscope_view.py 文件存在")
            
            with open("modules/endoscope_view.py", "r", encoding="utf-8") as f:
                content = f.read()
                
            # 检查关键方法
            methods = ["update_image", "clear_image", "start_algorithm", "stop_algorithm"]
            for method in methods:
                if f"def {method}" in content:
                    print(f"  ✅ {method} 方法存在")
                else:
                    print(f"  ❌ {method} 方法缺失")
                    
            # 检查图像显示相关代码
            if "QGraphicsView" in content:
                print("  ✅ 使用QGraphicsView显示图像")
            else:
                print("  ⚠️ 未找到QGraphicsView相关代码")
                
        else:
            print("❌ endoscope_view.py 文件不存在")
            
    except Exception as e:
        print(f"❌ 检查内窥镜视图组件失败: {e}")

def main():
    print("🔍 面板B图像显示问题诊断")
    print("=" * 80)
    
    print("📋 **问题现象**:")
    print("❌ 面板B启动算法后不显示照片")
    print("❌ 图像区域保持空白状态")
    print("❌ 没有图像切换效果")
    print()
    
    # 检查图像文件
    image_results = check_image_files()
    
    # 检查内窥镜视图组件
    check_endoscope_view()
    
    print("\n🔍 **可能的问题原因**:")
    print("=" * 60)
    
    # 分析图像文件问题
    for hole_id, result in image_results.items():
        if not result.get("exists", False):
            print(f"❌ {hole_id} 图像目录不存在")
        elif result.get("error"):
            print(f"❌ {hole_id} 目录读取错误: {result['error']}")
        elif result.get("png_count", 0) == 0:
            print(f"❌ {hole_id} 目录中没有PNG图像文件")
        else:
            print(f"✅ {hole_id} 有 {result['png_count']} 个PNG图像文件")
    
    print("\n🔧 **诊断步骤**:")
    print("=" * 60)
    
    print("步骤1: 检查控制台输出")
    print("  启动程序后查看控制台是否有以下信息:")
    print("  - '🔧 孔位数据映射初始化'")
    print("  - '📂 图像目录存在: True/False'")
    print("  - '✅ 为孔位 H00001 加载了 X 张内窥镜图片'")
    print()
    
    print("步骤2: 测试图像加载")
    print("  1. 选择孔位H00001")
    print("  2. 观察控制台输出:")
    print("     - '📸 显示第一张内窥镜图像'")
    print("     - '✅ 显示内窥镜图片: xxx.png'")
    print("  3. 如果有错误，记录具体错误信息")
    print()
    
    print("步骤3: 测试算法启动")
    print("  1. 点击面板B的'启动算法'按钮")
    print("  2. 观察控制台输出:")
    print("     - '🚀 启动面板B图像处理算法'")
    print("     - '✅ 图像切换功能已启用'")
    print("  3. 启动面板A观察图像是否切换")
    print()
    
    print("🛠️ **修复建议**:")
    print("=" * 60)
    
    # 根据检查结果给出建议
    all_good = True
    for hole_id, result in image_results.items():
        if not result.get("exists", False) or result.get("png_count", 0) == 0:
            all_good = False
            break
    
    if all_good:
        print("✅ 图像文件检查正常，问题可能在于:")
        print("1. 🔄 图像切换功能未启用")
        print("   解决: 确保点击'启动算法'按钮")
        print()
        print("2. 🖼️ 图像显示组件问题")
        print("   解决: 检查endoscope_view.py的update_image方法")
        print()
        print("3. 📊 数据同步问题")
        print("   解决: 确保面板A和B同时启动")
        print()
    else:
        print("❌ 发现图像文件问题，需要修复:")
        for hole_id, result in image_results.items():
            if not result.get("exists", False):
                print(f"1. 创建目录: Data/{hole_id}/BISDM/result")
            elif result.get("png_count", 0) == 0:
                print(f"2. 添加PNG图像文件到: Data/{hole_id}/BISDM/result")
    
    print("\n🧪 **测试脚本**:")
    print("=" * 60)
    print("创建简单的测试脚本验证图像显示:")
    print()
    print("```python")
    print("# 测试图像文件访问")
    print("import os")
    print("from PySide6.QtWidgets import QApplication")
    print("from PySide6.QtGui import QPixmap")
    print()
    print("app = QApplication([])")
    print("base_dir = os.getcwd()")
    print("image_path = os.path.join(base_dir, 'Data/H00001/BISDM/result')")
    print("if os.path.exists(image_path):")
    print("    files = [f for f in os.listdir(image_path) if f.endswith('.png')]")
    print("    if files:")
    print("        test_image = os.path.join(image_path, files[0])")
    print("        pixmap = QPixmap(test_image)")
    print("        print(f'图像加载: {not pixmap.isNull()}')")
    print("        print(f'图像尺寸: {pixmap.width()}x{pixmap.height()}')")
    print("```")
    print()
    
    print("🎯 **预期修复效果**:")
    print("=" * 60)
    print("修复后应该看到:")
    print("✅ 选择孔位后面板B显示第一张图像")
    print("✅ 启动算法后图像切换功能启用")
    print("✅ 面板A播放时图像根据进度切换")
    print("✅ 控制台输出正确的图像切换信息")
    print()
    
    print("🚀 **下一步操作**:")
    print("=" * 60)
    print("1. 运行程序并按照诊断步骤检查")
    print("2. 记录控制台的详细输出信息")
    print("3. 如果图像文件缺失，请添加测试图像")
    print("4. 如果仍有问题，提供具体的错误信息")

if __name__ == "__main__":
    main()
