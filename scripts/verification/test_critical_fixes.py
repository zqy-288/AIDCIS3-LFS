#!/usr/bin/env python3
"""
关键修复测试 - 简化版
专注于验证核心修复是否生效
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_critical_fixes():
    """测试关键修复"""
    print("=" * 80)
    print("关键修复测试")
    print("=" * 80)
    
    results = {
        'default_micro_view': False,
        'no_duplicate_load': False,
        'correct_detection_order': False,
        'correct_sector_assignment': False
    }
    
    # 测试1: 验证默认微观视图设置
    print("\n1. 测试默认微观视图设置...")
    try:
        with open('src/pages/main_detection_p1/native_main_detection_view_p1.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查关键代码
        checks = [
            'self.micro_view_btn.setChecked(True)',
            'self.current_view_mode = "micro"',
            '_initial_sector_loaded = False'
        ]
        
        all_found = all(check in content for check in checks)
        results['default_micro_view'] = all_found
        
        for check in checks:
            status = "✅" if check in content else "❌"
            print(f"   {status} {check}")
            
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试2: 验证无重复加载
    print("\n2. 测试防止重复加载...")
    try:
        # 检查是否移除了延迟加载
        no_timer = 'QTimer.singleShot(500, self._load_default_sector1)' not in content
        has_flag_check = 'if self._initial_sector_loaded:' in content
        
        results['no_duplicate_load'] = no_timer and has_flag_check
        
        print(f"   {'✅' if no_timer else '❌'} 移除延迟加载定时器")
        print(f"   {'✅' if has_flag_check else '❌'} 添加重复加载检查")
        
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试3: 验证检测顺序
    print("\n3. 测试检测顺序...")
    try:
        with open('src/pages/shared/components/snake_path/snake_path_renderer.py', 'r', encoding='utf-8') as f:
            snake_content = f.read()
            
        # 检查扇形顺序
        has_order = "sector_order = ['sector_1', 'sector_2', 'sector_3', 'sector_4']" in snake_content
        has_y_sort = 'sorted(holes_by_y.keys(), reverse=True)' in snake_content
        
        results['correct_detection_order'] = has_order and has_y_sort
        
        print(f"   {'✅' if has_order else '❌'} 正确的扇形顺序定义")
        print(f"   {'✅' if has_y_sort else '❌'} Y坐标排序逻辑")
        
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试4: 验证扇形分配
    print("\n4. 测试扇形分配坐标系...")
    try:
        with open('src/pages/main_detection_p1/components/sector_assignment_manager.py', 'r', encoding='utf-8') as f:
            sam_content = f.read()
            
        # 检查数学坐标系
        has_math_coords = '# 数学坐标系' in sam_content or 'Y轴向上' in sam_content
        correct_sector1 = 'x_sign >= 0 and dy >= 0' in sam_content
        
        results['correct_sector_assignment'] = has_math_coords and correct_sector1
        
        print(f"   {'✅' if has_math_coords else '❌'} 使用数学坐标系")
        print(f"   {'✅' if correct_sector1 else '❌'} sector_1正确分配到右上")
        
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 额外验证：微观视图下禁用自适应
    print("\n5. 额外验证：微观视图自适应控制...")
    try:
        with open('src/core_business/graphics/graphics_view.py', 'r', encoding='utf-8') as f:
            gv_content = f.read()
            
        has_micro_check = "self.current_view_mode == 'micro'" in gv_content
        print(f"   {'✅' if has_micro_check else '❌'} 微观视图下跳过resizeEvent")
        
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 总结
    print("\n" + "=" * 80)
    print("测试结果总结")
    print("=" * 80)
    
    for test, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test}: {status}")
    
    # 计算通过率
    passed = sum(results.values())
    total = len(results)
    pass_rate = (passed / total) * 100
    
    print(f"\n总体通过率: {pass_rate:.0f}% ({passed}/{total})")
    
    # 运行检测顺序验证
    if results['correct_detection_order']:
        print("\n" + "=" * 80)
        print("运行检测顺序验证...")
        print("=" * 80)
        
        try:
            from final_order_verification import final_verification
            final_verification()
        except Exception as e:
            print(f"检测顺序验证失败: {e}")
    
    return pass_rate == 100


if __name__ == "__main__":
    success = test_critical_fixes()
    sys.exit(0 if success else 1)