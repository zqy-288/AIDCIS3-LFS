#!/usr/bin/env python3
"""
修复验证和路径更新测试脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("🔧 修复验证和路径更新")
    print("=" * 60)
    
    print("✅ **问题修复状态**:")
    print("=" * 50)
    print("1. 🔄 图表更新异常: 已添加异常处理")
    print("2. 📂 图像路径更新: 已更新为新的路径结构")
    print("3. 🔧 导入问题修复: 已修复os模块导入")
    print("4. 🎯 孔位信息同步: 已添加强制刷新机制")
    print()
    
    print("📂 **新的图像路径配置**:")
    print("=" * 50)
    
    # 获取当前工作目录
    base_dir = os.getcwd()
    
    h00001_image_path = os.path.join(base_dir, "Data/H00001/BISDM/result")
    h00002_image_path = os.path.join(base_dir, "Data/H00002/BISDM/result")
    
    print("H00001:")
    print(f"  📄 CSV数据: data/H00001/CCIDM/")
    print(f"  🖼️ 图像数据: {h00001_image_path}")
    print(f"  📂 目录存在: {os.path.exists(h00001_image_path)}")
    print()
    
    print("H00002:")
    print(f"  📄 CSV数据: data/H00002/CCIDM/")
    print(f"  🖼️ 图像数据: {h00002_image_path}")
    print(f"  📂 目录存在: {os.path.exists(h00002_image_path)}")
    print()
    
    print("🔍 **路径检查结果**:")
    print("=" * 50)
    
    # 检查所有相关路径
    paths_to_check = [
        ("H00001 CSV", "data/H00001/CCIDM"),
        ("H00002 CSV", "data/H00002/CCIDM"),
        ("H00001 图像", h00001_image_path),
        ("H00002 图像", h00002_image_path),
    ]
    
    all_paths_exist = True
    for name, path in paths_to_check:
        exists = os.path.exists(path)
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"{name}: {status}")
        print(f"  路径: {path}")
        
        if exists and os.path.isdir(path):
            try:
                files = os.listdir(path)
                if name.endswith("CSV"):
                    csv_files = [f for f in files if f.endswith('.csv')]
                    print(f"  📄 CSV文件数量: {len(csv_files)}")
                    if csv_files:
                        print(f"  📄 示例文件: {csv_files[0]}")
                elif name.endswith("图像"):
                    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    print(f"  🖼️ 图像文件数量: {len(image_files)}")
                    if image_files:
                        print(f"  🖼️ 示例文件: {image_files[0]}")
            except Exception as e:
                print(f"  ⚠️ 读取目录失败: {e}")
        
        if not exists:
            all_paths_exist = False
        print()
    
    print("🎯 **测试建议**:")
    print("=" * 50)
    
    if all_paths_exist:
        print("✅ 所有路径都存在，可以进行完整测试:")
        print("1. 启动程序: python main.py")
        print("2. 测试主检测界面孔位信息显示")
        print("3. 测试实时监控界面孔位选择功能")
        print("4. 验证面板A和面板B的数据加载")
    else:
        print("⚠️ 部分路径不存在，请先创建缺失的目录:")
        print()
        for name, path in paths_to_check:
            if not os.path.exists(path):
                print(f"创建目录: mkdir -p '{path}'")
        print()
        print("然后将对应的数据文件放入相应目录。")
    
    print()
    print("🧪 **具体测试步骤**:")
    print("=" * 50)
    print("步骤1: 测试孔位信息显示修复")
    print("  1. 启动程序")
    print("  2. 切换到'主检测视图'")
    print("  3. 按Ctrl+T加载DXF")
    print("  4. 搜索H00001")
    print("  5. 观察左下角是否显示孔位信息")
    print("  6. 检查右下角调试日志")
    print()
    
    print("步骤2: 测试面板A/B孔位选择")
    print("  1. 从主检测界面点击'实时监控'")
    print("  2. 观察顶部状态栏的孔位选择控件")
    print("  3. 测试下拉选择H00001/H00002")
    print("  4. 测试快速切换按钮")
    print("  5. 观察面板A图表和面板B图像的变化")
    print()
    
    print("步骤3: 验证新的图像路径")
    print("  1. 在实时监控界面选择H00001")
    print("  2. 观察面板B是否显示来自新路径的图像")
    print("  3. 切换到H00002")
    print("  4. 验证图像是否从新路径加载")
    print()
    
    print("🔍 **预期现象**:")
    print("=" * 50)
    print("1. 左下角孔位信息正确显示")
    print("2. 实时监控界面顶部有孔位选择控件")
    print("3. 面板A显示CSV数据图表")
    print("4. 面板B显示来自新路径的内窥镜图像")
    print("5. 孔位切换功能正常工作")
    print("6. 程序启动时不再有图表更新异常")
    print()
    
    print("🚨 **如果遇到问题**:")
    print("=" * 50)
    print("1. 检查数据文件是否存在于正确路径")
    print("2. 查看右下角日志的详细错误信息")
    print("3. 确认图像文件格式为PNG/JPG")
    print("4. 验证CSV文件包含'测量序号'和'计算直径'列")
    print()
    
    print("现在请测试修复后的功能！🚀")

if __name__ == "__main__":
    main()
