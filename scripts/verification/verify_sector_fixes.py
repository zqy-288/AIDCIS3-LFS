#!/usr/bin/env python3
"""
验证扇形分隔线修复的代码检查工具
检查关键文件是否包含正确的修复代码
"""

import sys
import os
from pathlib import Path

def check_file_content(file_path, expected_patterns, description):
    """检查文件是否包含预期的内容模式"""
    try:
        if not os.path.exists(file_path):
            print(f"❌ {description}: 文件不存在 - {file_path}")
            return False, []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        found_patterns = []
        missing_patterns = []
        
        for pattern_name, pattern in expected_patterns.items():
            if pattern in content:
                found_patterns.append(pattern_name)
                print(f"✅ {description}: 找到 {pattern_name}")
            else:
                missing_patterns.append(pattern_name)
                print(f"⚠️ {description}: 缺少 {pattern_name}")
        
        success = len(missing_patterns) == 0
        status = "✅ 完全修复" if success else f"⚠️ 缺少 {len(missing_patterns)} 项修复"
        print(f"📊 {description}: {status}")
        
        return success, found_patterns
        
    except Exception as e:
        print(f"❌ {description}: 检查失败 - {e}")
        return False, []

def main():
    """主验证函数"""
    print("🔍 验证扇形分隔线修复状态")
    print("=" * 50)
    
    # 定义要检查的文件和预期内容
    checks = [
        {
            "file": "src/pages/main_detection_p1/components/graphics/sector_highlight_item.py",
            "description": "Pages目录扇形高亮组件",
            "patterns": {
                "默认可见调用": "self.highlight(True)",
                "灰色虚线样式": "QColor(128, 128, 128), 2, Qt.DashLine",
                "透明填充": "QColor(255, 255, 255, 0)"
            }
        },
        {
            "file": "src/pages/main_detection_p1/components/graphics/complete_panorama_widget.py", 
            "description": "Pages目录全景图组件",
            "patterns": {
                "深灰色分隔线": "QColor(80, 80, 80, 200)",
                "分隔线宽度": "setWidth(3)",
                "实线样式": "Qt.SolidLine"
            }
        },
        {
            "file": "src/pages/main_detection_p1/native_main_detection_view_p1.py",
            "description": "主检测页面导入",
            "patterns": {
                "正确导入路径": "from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget"
            }
        }
    ]
    
    all_passed = True
    summary = []
    
    for check in checks:
        print(f"\n🔍 检查: {check['description']}")
        print(f"📁 文件: {check['file']}")
        
        success, found = check_file_content(
            check['file'], 
            check['patterns'], 
            check['description']
        )
        
        summary.append({
            "name": check['description'],
            "success": success,
            "found_count": len(found),
            "total_count": len(check['patterns'])
        })
        
        if not success:
            all_passed = False
    
    # 打印总结
    print("\n" + "=" * 50)
    print("📊 修复验证总结:")
    
    for item in summary:
        status = "✅" if item['success'] else "⚠️"
        print(f"{status} {item['name']}: {item['found_count']}/{item['total_count']} 项修复已应用")
    
    if all_passed:
        print("\n🎉 所有修复都已正确应用!")
        print("✅ 扇形分隔线应该能正常显示:")
        print("   • 深灰色十字分隔线 (alpha=200, 宽度3px)")
        print("   • 灰色虚线扇形边界 (默认可见)")
        print("   • 四个清晰的扇形区域")
        print("\n💡 建议: 重新运行主程序查看效果")
    else:
        failed_count = sum(1 for item in summary if not item['success'])
        print(f"\n⚠️ 有 {failed_count} 个文件的修复不完整")
        print("建议检查并手动应用缺失的修复")
    
    # 额外检查：循环导入问题
    print(f"\n🔍 检查循环导入问题...")
    circular_import_indicators = [
        ("src/modules/panorama_view/__init__.py", "CompletePanoramaWidget"),
        ("src/pages/main_detection_p1/components/graphics/dynamic_sector_view.py", "from src.modules.panorama_view import CompletePanoramaWidget")
    ]
    
    for file_path, pattern in circular_import_indicators:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if pattern in content:
                print(f"⚠️ 发现可能的循环导入: {file_path}")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)