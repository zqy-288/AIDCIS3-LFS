#!/usr/bin/env python3
"""
测试主程序集成
验证新的缺陷标注工具是否能正确集成到主程序中
"""

import sys
import os
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试导入是否正常"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试核心模块导入
        from modules.defect_annotation_model import DefectAnnotation
        print("  ✅ DefectAnnotation 导入成功")
        
        from modules.image_scanner import ImageScanner
        print("  ✅ ImageScanner 导入成功")
        
        from modules.yolo_file_manager import YOLOFileManager
        print("  ✅ YOLOFileManager 导入成功")
        
        from modules.defect_category_manager import DefectCategoryManager
        print("  ✅ DefectCategoryManager 导入成功")
        
        from modules.annotation_graphics_view import AnnotationGraphicsView
        print("  ✅ AnnotationGraphicsView 导入成功")
        
        from modules.defect_annotation_tool import DefectAnnotationTool
        print("  ✅ DefectAnnotationTool 导入成功")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def test_main_window_integration():
    """测试主窗口集成"""
    print("\n🔍 测试主窗口集成...")
    
    try:
        # 测试PySide6导入
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        
        # 创建应用程序实例（如果不存在）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 测试主窗口导入
        from main_window.main_window import MainWindow
        print("  ✅ MainWindow 导入成功")
        
        # 测试创建主窗口（不显示）
        window = MainWindow()
        print("  ✅ MainWindow 创建成功")
        
        # 检查标注工具是否正确集成
        if hasattr(window, 'annotation_tab'):
            print("  ✅ 标注工具选项卡存在")
            
            # 检查标注工具类型
            from modules.defect_annotation_tool import DefectAnnotationTool
            if isinstance(window.annotation_tab, DefectAnnotationTool):
                print("  ✅ 标注工具类型正确")
                return True
            else:
                print(f"  ❌ 标注工具类型错误: {type(window.annotation_tab)}")
                return False
        else:
            print("  ❌ 标注工具选项卡不存在")
            return False
            
    except Exception as e:
        print(f"  ❌ 主窗口集成失败: {e}")
        return False

def test_defect_annotation_tool():
    """测试缺陷标注工具功能"""
    print("\n🔍 测试缺陷标注工具功能...")
    
    try:
        from PySide6.QtWidgets import QApplication
        
        # 创建应用程序实例（如果不存在）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        from modules.defect_annotation_tool import DefectAnnotationTool
        
        # 创建标注工具实例
        tool = DefectAnnotationTool()
        print("  ✅ DefectAnnotationTool 实例创建成功")
        
        # 检查核心组件
        if hasattr(tool, 'image_scanner'):
            print("  ✅ ImageScanner 组件存在")
        else:
            print("  ❌ ImageScanner 组件缺失")
            
        if hasattr(tool, 'yolo_manager'):
            print("  ✅ YOLOFileManager 组件存在")
        else:
            print("  ❌ YOLOFileManager 组件缺失")
            
        if hasattr(tool, 'category_manager'):
            print("  ✅ DefectCategoryManager 组件存在")
        else:
            print("  ❌ DefectCategoryManager 组件缺失")
            
        if hasattr(tool, 'graphics_view'):
            print("  ✅ AnnotationGraphicsView 组件存在")
        else:
            print("  ❌ AnnotationGraphicsView 组件缺失")
            
        # 检查UI组件
        ui_components = [
            'hole_combo', 'image_list', 'pan_btn', 'annotate_btn', 'edit_btn',
            'defect_combo', 'save_btn', 'load_btn', 'defect_table'
        ]
        
        missing_components = []
        for component in ui_components:
            if hasattr(tool, component):
                print(f"  ✅ UI组件 {component} 存在")
            else:
                missing_components.append(component)
                print(f"  ❌ UI组件 {component} 缺失")
                
        if len(missing_components) == 0:
            print("  ✅ 所有UI组件都存在")
            return True
        else:
            print(f"  ❌ 缺失 {len(missing_components)} 个UI组件")
            return False
            
    except Exception as e:
        print(f"  ❌ 缺陷标注工具测试失败: {e}")
        return False

def test_data_directory():
    """测试数据目录结构"""
    print("\n🔍 测试数据目录结构...")
    
    data_dir = Path("Data")
    if data_dir.exists():
        print(f"  ✅ Data目录存在: {data_dir.absolute()}")
        
        # 查找孔位目录
        hole_dirs = []
        for item in data_dir.iterdir():
            if item.is_dir() and item.name.startswith('H') and item.name[1:].isdigit():
                hole_dirs.append(item.name)
                
        if hole_dirs:
            print(f"  ✅ 发现孔位目录: {sorted(hole_dirs)}")
            
            # 检查第一个孔位的结构
            first_hole = sorted(hole_dirs)[0]
            result_dir = data_dir / first_hole / "BISDM" / "result"
            
            if result_dir.exists():
                print(f"  ✅ 孔位结构正确: {first_hole}/BISDM/result")
                
                # 查找图像文件
                image_files = list(result_dir.glob("*.jpg")) + list(result_dir.glob("*.png"))
                if image_files:
                    print(f"  ✅ 发现图像文件: {len(image_files)} 个")
                    return True
                else:
                    print("  ⚠️ 未发现图像文件")
                    return True  # 结构正确，只是没有图像文件
            else:
                print(f"  ❌ 孔位结构错误: {first_hole}")
                return False
        else:
            print("  ⚠️ 未发现孔位目录")
            return True  # 目录存在，只是没有孔位数据
    else:
        print("  ⚠️ Data目录不存在，将使用默认配置")
        return True

def main():
    """主测试函数"""
    print("🧪 缺陷标注工具集成测试")
    print("=" * 50)
    
    test_results = []
    
    # 执行各项测试
    test_results.append(test_imports())
    test_results.append(test_main_window_integration())
    test_results.append(test_defect_annotation_tool())
    test_results.append(test_data_directory())
    
    # 总结测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    print(f"📈 成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有测试通过! 缺陷标注工具已成功集成到主程序")
        print("\n🚀 可以运行主程序:")
        print("   python main.py")
        return True
    else:
        print("\n⚠️ 部分测试失败，需要检查集成问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
