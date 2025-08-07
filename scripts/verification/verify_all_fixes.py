#!/usr/bin/env python3
"""
验证所有修复是否正确实施
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def verify_dxf_parser_fix():
    """验证DXF解析器修复"""
    print("=" * 60)
    print("1. 验证DXF解析器修复")
    print("=" * 60)
    
    # 检查代码文件
    dxf_parser_file = "src/core_business/dxf_parser.py"
    with open(dxf_parser_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("导入HoleNumberingService", "from src.core_business.hole_numbering_service import HoleNumberingService" in content),
        ("创建HoleNumberingService实例", "numbering_service = HoleNumberingService()" in content),
        ("调用apply_numbering", "numbering_service.apply_numbering(temp_collection)" in content),
        ("设置no_ids为False", "'no_ids': False" in content),
        ("使用修改后的temp_collection", "hole_collection = temp_collection" in content),
    ]
    
    all_passed = True
    for name, result in checks:
        status = "✅" if result else "❌"
        if not result:
            all_passed = False
        print(f"   {status} {name}")
    
    # 测试HoleNumberingService创建
    try:
        from src.core_business.hole_numbering_service import HoleNumberingService
        service = HoleNumberingService()
        print("   ✅ HoleNumberingService实例化成功")
    except Exception as e:
        print(f"   ❌ HoleNumberingService实例化失败: {e}")
        all_passed = False
    
    return all_passed

def verify_micro_view_scale_fix():
    """验证微观视图缩放修复"""
    print("\n" + "=" * 60)
    print("2. 验证微观视图缩放修复")
    print("=" * 60)
    
    # 检查graphics_view.py
    graphics_view_file = "src/core_business/graphics/graphics_view.py"
    with open(graphics_view_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("缩放锁机制", "if getattr(self, '_is_fitting', False):" in content),
        ("扇形适配标志检查", "if getattr(self, '_fitted_to_sector', False):" in content),
        ("新的最小缩放0.5", "min_micro_scale = 0.5" in content),
        ("新的最大缩放2.0", "max_micro_scale = 2.0" in content),
        ("标志重置", "self._fitted_to_sector = False" in content),
    ]
    
    all_passed = True
    for name, result in checks:
        status = "✅" if result else "❌"
        if not result:
            all_passed = False
        print(f"   {status} {name}")
    
    # 检查native_main_detection_view_p1.py中的标志设置
    native_view_file = "src/pages/main_detection_p1/native_main_detection_view_p1.py"
    with open(native_view_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    flag_checks = [
        ("设置_fitted_to_sector标志", "graphics_view._fitted_to_sector = True" in content),
        ("延迟恢复disable_auto_fit", "QTimer.singleShot(500, lambda: setattr(graphics_view, 'disable_auto_fit', False))" in content),
    ]
    
    for name, result in flag_checks:
        status = "✅" if result else "❌"
        if not result:
            all_passed = False
        print(f"   {status} {name}")
    
    return all_passed

def verify_snake_path_priority_fix():
    """验证蛇形路径优先级修复"""
    print("\n" + "=" * 60)
    print("3. 验证蛇形路径优先级修复")
    print("=" * 60)
    
    # 检查snake_path_renderer.py
    snake_path_file = "src/pages/shared/components/snake_path/snake_path_renderer.py"
    with open(snake_path_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("R164特殊处理注释", "特殊处理R164行，确保BC098R164+BC102R164作为第一个配对" in content),
        ("R164行判断", "if row_num == 164:" in content),
        ("查找列号98和102", "col98_hole = holes_by_col.get(98)" in content and "col102_hole = holes_by_col.get(102)" in content),
        ("BC098R164+BC102R164配对创建", "hole1 = self._position_to_hole_data(col98_hole)" in content),
    ]
    
    all_passed = True
    for name, result in checks:
        status = "✅" if result else "❌"
        if not result:
            all_passed = False
        print(f"   {status} {name}")
    
    return all_passed

def main():
    """运行所有验证"""
    print("🔍 验证所有修复实施情况\n")
    
    fix1 = verify_dxf_parser_fix()
    fix2 = verify_micro_view_scale_fix() 
    fix3 = verify_snake_path_priority_fix()
    
    print("\n" + "=" * 60)
    print("📊 验证总结")
    print("=" * 60)
    
    results = [
        ("ID格式统一修复", fix1),
        ("微观视图缩放修复", fix2),
        ("检测配对优先级修复", fix3),
    ]
    
    all_good = True
    for name, result in results:
        status = "✅" if result else "❌"
        if not result:
            all_good = False
        print(f"{status} {name}")
    
    print(f"\n{'🎉 所有修复已正确实施！' if all_good else '⚠️  发现问题，请检查上述失败项'}")
    print("建议：在实际应用中测试CAP1000.dxf文件加载")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)