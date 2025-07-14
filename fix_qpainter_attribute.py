#!/usr/bin/env python3
"""
修复 QPainter.HighQualityAntialiasing 属性错误
"""

import re

def fix_qpainter_attribute():
    """修复 QPainter 属性错误"""
    print("🔧 修复 QPainter.HighQualityAntialiasing 错误...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除或注释掉 HighQualityAntialiasing 行
    # 这个属性在 PySide6 中已被弃用
    content = re.sub(
        r'mini_view\.setRenderHint\(QPainter\.HighQualityAntialiasing, True\)',
        '# mini_view.setRenderHint(QPainter.HighQualityAntialiasing, True)  # 在 PySide6 中已弃用',
        content
    )
    
    print("✅ 注释掉了 HighQualityAntialiasing")
    
    # 确保其他渲染提示正确
    # Antialiasing 已经包含了高质量抗锯齿
    if 'QPainter.Antialiasing' in content:
        print("✅ 已有 QPainter.Antialiasing，这已经足够")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复完成")

def check_qpainter_usage():
    """检查所有 QPainter 使用情况"""
    print("\n🔍 检查其他 QPainter 使用...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有 QPainter 相关的行
    import re
    painter_lines = re.findall(r'.*QPainter\..*', content)
    
    print(f"找到 {len(painter_lines)} 处 QPainter 使用：")
    for line in painter_lines[:5]:  # 只显示前5个
        print(f"  - {line.strip()}")
    
    # 检查是否还有其他可能有问题的属性
    problematic_attrs = [
        'HighQualityAntialiasing',
        'NonCosmeticDefaultPen',
        'Qt4CompatiblePainting'
    ]
    
    problems_found = False
    for attr in problematic_attrs:
        if f'QPainter.{attr}' in content:
            print(f"⚠️ 发现可能有问题的属性: QPainter.{attr}")
            problems_found = True
    
    if not problems_found:
        print("✅ 没有发现其他有问题的 QPainter 属性")

def main():
    print("=" * 60)
    print("修复 QPainter 属性错误")
    print("=" * 60)
    
    fix_qpainter_attribute()
    check_qpainter_usage()
    
    print("\n✅ 修复完成！可以重新运行程序了。")
    print("\n注意：QPainter.Antialiasing 已经提供了足够的抗锯齿效果。")

if __name__ == "__main__":
    main()