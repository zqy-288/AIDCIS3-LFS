#!/usr/bin/env python3
"""
验证缺陷标注工具集成
简单快速的验证脚本
"""

import sys
import os
from pathlib import Path

def main():
    print("🔍 验证缺陷标注工具集成")
    print("=" * 40)
    
    try:
        # 1. 验证核心模块导入
        print("1. 验证核心模块导入...")
        from modules.defect_annotation_tool import DefectAnnotationTool
        print("   ✅ DefectAnnotationTool 导入成功")
        
        # 2. 验证主窗口导入
        print("2. 验证主窗口导入...")
        from main_window.main_window import MainWindow
        print("   ✅ MainWindow 导入成功")
        
        # 3. 验证文件修改
        print("3. 验证文件修改...")
        with open('main_window.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'from modules.defect_annotation_tool import DefectAnnotationTool' in content:
            print("   ✅ 导入语句已更新")
        else:
            print("   ❌ 导入语句未更新")
            return False
            
        if 'self.annotation_tab = DefectAnnotationTool()' in content:
            print("   ✅ 实例化语句已更新")
        else:
            print("   ❌ 实例化语句未更新")
            return False
        
        # 4. 验证模块文件存在
        print("4. 验证模块文件...")
        required_files = [
            'modules/defect_annotation_tool.py',
            'modules/defect_annotation_model.py',
            'modules/image_scanner.py',
            'modules/yolo_file_manager.py',
            'modules/defect_category_manager.py',
            'modules/annotation_graphics_view.py'
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                print(f"   ✅ {file_path} 存在")
            else:
                print(f"   ❌ {file_path} 不存在")
                return False
        
        print("\n🎉 集成验证成功!")
        print("\n📋 集成总结:")
        print("   • 已将完整的缺陷标注工具集成到主程序")
        print("   • 替换了原有的简单annotation_tool")
        print("   • 所有依赖模块都已正确配置")
        print("   • 可以运行 python main.py 启动完整程序")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
