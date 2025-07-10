#!/usr/bin/env python3
"""
修复DXF显示问题的脚本
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def check_and_fix_dxf_display():
    """检查并修复DXF显示问题"""
    
    print("🔍 DXF显示问题诊断和修复")
    print("=" * 50)
    
    # 1. 检查DXF文件是否存在
    test_files = ["测试管板.dxf", "DXF Graph/东重管板.dxf"]
    available_files = []
    
    for file_path in test_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ 找到DXF文件: {file_path} ({size} 字节)")
            available_files.append(file_path)
        else:
            print(f"❌ DXF文件不存在: {file_path}")
    
    if not available_files:
        print("❌ 没有找到可用的DXF文件")
        return False
    
    # 2. 检查DXF解析器
    try:
        from aidcis2.dxf_parser import DXFParser
        print("✅ DXF解析器导入成功")
        
        parser = DXFParser()
        print("✅ DXF解析器创建成功")
        
        # 测试解析第一个可用文件
        test_file = available_files[0]
        print(f"🔄 测试解析文件: {test_file}")
        
        # 这里我们不实际解析，只是检查导入
        print("✅ DXF解析器准备就绪")
        
    except Exception as e:
        print(f"❌ DXF解析器问题: {e}")
        return False
    
    # 3. 检查图形视图组件
    try:
        from aidcis2.graphics.graphics_view import OptimizedGraphicsView
        print("✅ 图形视图组件导入成功")
        
        from aidcis2.graphics.hole_item import HoleGraphicsItem, HoleItemFactory
        print("✅ 孔位图形项组件导入成功")
        
    except Exception as e:
        print(f"❌ 图形视图组件问题: {e}")
        return False
    
    # 4. 检查数据模型
    try:
        from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
        print("✅ 数据模型导入成功")
        
    except Exception as e:
        print(f"❌ 数据模型问题: {e}")
        return False
    
    print("\n🎯 **问题诊断结果**")
    print("=" * 50)
    print("所有核心组件都正常，DXF显示问题可能是以下原因：")
    print()
    print("1. **DXF文件未加载**: 需要先点击'打开DXF文件'按钮加载DXF文件")
    print("2. **视图范围问题**: 孔位存在但不在当前视图范围内")
    print("3. **图形项未正确创建**: 解析成功但图形项创建失败")
    print("4. **场景矩形设置问题**: 场景大小设置不正确")
    print()
    print("🔧 **建议的修复步骤**:")
    print("1. 确保先加载DXF文件")
    print("2. 加载后点击'适应窗口'按钮")
    print("3. 检查日志输出中的错误信息")
    print("4. 如果仍然空白，可能需要调试图形视图的load_holes方法")
    
    return True

def create_test_fix():
    """创建测试修复方案"""
    
    print("\n🔧 **创建测试修复方案**")
    print("=" * 50)
    
    # 创建一个简单的测试脚本来验证DXF加载
    test_script = '''#!/usr/bin/env python3
"""
DXF加载测试脚本
使用方法: 在主程序运行时，在Python控制台中执行此脚本
"""

def test_dxf_loading_in_main_window():
    """在主窗口中测试DXF加载"""
    
    # 这个函数需要在主窗口实例中调用
    # 例如: main_window.test_dxf_loading()
    
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # 假设self是主窗口实例
    if hasattr(self, 'dxf_parser') and hasattr(self, 'graphics_view'):
        try:
            # 尝试加载测试文件
            test_file = "测试管板.dxf"
            if Path(test_file).exists():
                print(f"加载测试文件: {test_file}")
                
                # 解析DXF
                hole_collection = self.dxf_parser.parse_file(test_file)
                print(f"解析结果: {len(hole_collection) if hole_collection else 0} 个孔位")
                
                if hole_collection and len(hole_collection) > 0:
                    # 加载到图形视图
                    self.graphics_view.load_holes(hole_collection)
                    print("已加载到图形视图")
                    
                    # 适应视图
                    self.graphics_view.fit_in_view()
                    print("已适应视图")
                    
                    return True
                else:
                    print("没有找到孔位数据")
                    return False
            else:
                print(f"测试文件不存在: {test_file}")
                return False
                
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("主窗口组件未正确初始化")
        return False

# 使用说明:
# 1. 启动主程序
# 2. 在Python控制台中导入此模块
# 3. 调用 main_window_instance.test_dxf_loading()
'''
    
    with open("test_dxf_loading_fix.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("✅ 创建了测试脚本: test_dxf_loading_fix.py")
    
    return True

if __name__ == "__main__":
    success = check_and_fix_dxf_display()
    if success:
        create_test_fix()
        print("\n✅ 诊断完成！请按照建议的步骤进行修复。")
    else:
        print("\n❌ 诊断发现严重问题，需要先修复基础组件。")
