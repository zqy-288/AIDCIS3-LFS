#!/usr/bin/env python3
"""
CSV路径问题修复测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🔧 CSV路径问题修复")
    print("=" * 60)
    
    print("✅ **问题分析**:")
    print("=" * 50)
    print("错误信息显示系统在寻找具体的CSV文件路径，")
    print("但我们的新实现应该是扫描目录中的CSV文件。")
    print()
    print("问题根源:")
    print("1. start_csv_data_import()方法在非自动播放模式下")
    print("   尝试使用旧的文件列表逻辑")
    print("2. load_data_for_hole()正确传递了file_path参数")
    print("3. 但start_csv_data_import(auto_play=True)被调用时")
    print("   可能触发了错误的代码路径")
    print()
    
    print("✅ **修复内容**:")
    print("=" * 50)
    print("1. 🔧 修复start_csv_data_import()方法")
    print("   - 区分自动播放和手动播放模式")
    print("   - 自动播放模式不重新加载数据")
    print("   - 手动播放模式检查文件列表可用性")
    print()
    print("2. 🗂️ 清理旧的文件列表配置")
    print("   - 移除硬编码的CSV文件列表")
    print("   - 使用新的孔位映射系统")
    print()
    print("3. 🔄 改进错误处理")
    print("   - 添加更好的错误检查")
    print("   - 提供更清晰的错误信息")
    print()
    
    print("📂 **当前路径配置**:")
    print("=" * 50)
    
    # 检查当前的数据路径
    base_dir = os.getcwd()
    
    csv_paths = {
        "H00001": "data/H00001/CCIDM",
        "H00002": "data/H00002/CCIDM"
    }
    
    image_paths = {
        "H00001": os.path.join(base_dir, "Data/H00001/BISDM/result"),
        "H00002": os.path.join(base_dir, "Data/H00002/BISDM/result")
    }
    
    print("CSV数据路径:")
    for hole_id, path in csv_paths.items():
        exists = os.path.exists(path)
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"  {hole_id}: {status}")
        print(f"    路径: {path}")
        
        if exists:
            try:
                files = os.listdir(path)
                csv_files = [f for f in files if f.endswith('.csv')]
                print(f"    📄 CSV文件: {len(csv_files)} 个")
                if csv_files:
                    print(f"    📄 文件名: {csv_files[0]}")
            except Exception as e:
                print(f"    ⚠️ 读取失败: {e}")
        print()
    
    print("图像数据路径:")
    for hole_id, path in image_paths.items():
        exists = os.path.exists(path)
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"  {hole_id}: {status}")
        print(f"    路径: {path}")
        
        if exists:
            try:
                files = os.listdir(path)
                image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                print(f"    🖼️ 图像文件: {len(image_files)} 个")
                if image_files:
                    print(f"    🖼️ 示例: {image_files[0]}")
            except Exception as e:
                print(f"    ⚠️ 读取失败: {e}")
        print()
    
    print("🧪 **测试步骤**:")
    print("=" * 50)
    print("现在请重新测试孔位选择功能:")
    print()
    print("步骤1: 启动程序")
    print("  python main.py")
    print()
    print("步骤2: 测试主检测界面")
    print("  1. 切换到'主检测视图'")
    print("  2. 按Ctrl+T加载DXF")
    print("  3. 搜索H00001")
    print("  4. 观察左下角孔位信息")
    print()
    print("步骤3: 测试实时监控界面")
    print("  1. 点击'实时监控'按钮")
    print("  2. 观察顶部孔位选择控件")
    print("  3. 测试下拉选择H00001")
    print("  4. 观察是否还有路径错误")
    print()
    print("步骤4: 测试孔位切换")
    print("  1. 在实时监控界面选择H00002")
    print("  2. 观察面板A和面板B的数据加载")
    print("  3. 验证没有文件路径错误")
    print()
    
    print("🔍 **预期现象**:")
    print("=" * 50)
    print("1. 不再出现'Not a directory'错误")
    print("2. 孔位选择功能正常工作")
    print("3. 面板A显示CSV数据图表")
    print("4. 面板B显示内窥镜图像")
    print("5. 孔位切换流畅无错误")
    print()
    
    print("🚨 **如果仍有问题**:")
    print("=" * 50)
    print("请检查:")
    print("1. 右下角日志的详细错误信息")
    print("2. 确认CSV文件确实存在于指定目录")
    print("3. 确认CSV文件格式正确")
    print("4. 检查文件权限是否正确")
    print()
    
    print("💡 **技术说明**:")
    print("=" * 50)
    print("修复原理:")
    print("1. load_data_for_hole()扫描目录查找CSV文件")
    print("2. 找到文件后调用load_csv_data(file_path=具体文件)")
    print("3. start_csv_data_import(auto_play=True)不重新加载")
    print("4. 避免了旧文件列表逻辑的干扰")
    print()
    
    print("🎉 **修复完成！**")
    print("现在请重新测试功能，应该不会再有路径错误了。")

if __name__ == "__main__":
    main()
