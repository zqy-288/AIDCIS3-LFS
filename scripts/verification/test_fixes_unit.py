#!/usr/bin/env python3
"""
定时器和遍历修复的单元测试（无GUI）
验证核心逻辑修复
"""

import sys
import logging
from pathlib import Path
import inspect

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_timer_constants():
    """测试定时器常量设置"""
    logger.info("🕐 测试1: 定时器常量")
    
    try:
        # 直接检查源码中的常量定义
        with open('src/pages/main_detection_p1/components/simulation_controller.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查定时器设置
        if 'pair_detection_time = 10000' in content:
            logger.info("   ✅ 主定时器设置正确: 10000ms")
        else:
            logger.error("   ❌ 主定时器设置错误")
            return False
            
        if 'status_change_time = 9500' in content:
            logger.info("   ✅ 状态变化定时器设置正确: 9500ms")
        else:
            logger.error("   ❌ 状态变化定时器设置错误")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"   ❌ 定时器常量测试失败: {e}")
        return False

def test_fallback_removal():
    """测试后备模式删除"""
    logger.info("🚫 测试2: 后备模式删除")
    
    try:
        with open('src/pages/main_detection_p1/components/simulation_controller.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否还有后备模式关键词
        fallback_indicators = [
            '后备方案',
            'hole_list.sort',
            'self.detection_units = hole_list',
            '单孔检测单元',
            'def _start_single_hole_detection'
        ]
        
        found_indicators = []
        for indicator in fallback_indicators:
            if indicator in content:
                found_indicators.append(indicator)
        
        if found_indicators:
            logger.warning(f"   ⚠️ 仍有后备模式代码: {found_indicators}")
            return False
        else:
            logger.info("   ✅ 后备模式代码已完全删除")
            return True
            
    except Exception as e:
        logger.error(f"   ❌ 后备模式检查失败: {e}")
        return False

def test_type_check_simplification():
    """测试类型检查简化"""
    logger.info("⚡ 测试3: 类型检查简化")
    
    try:
        with open('src/pages/main_detection_p1/components/simulation_controller.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计复杂的类型检查
        isinstance_count = content.count('isinstance(')
        hasattr_count = content.count('hasattr(')
        
        logger.info(f"   isinstance检查数量: {isinstance_count}")
        logger.info(f"   hasattr检查数量: {hasattr_count}")
        
        # 应该有显著减少
        total_checks = isinstance_count + hasattr_count
        
        if total_checks <= 10:  # 允许少量必要的检查
            logger.info("   ✅ 类型检查已简化")
            return True
        else:
            logger.warning(f"   ⚠️ 类型检查仍然较多: {total_checks}")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ 类型检查测试失败: {e}")
        return False

def test_hole_extraction_logic():
    """测试孔位提取逻辑简化"""
    logger.info("🔗 测试4: 孔位提取逻辑")
    
    try:
        with open('src/pages/main_detection_p1/components/simulation_controller.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找孔位提取部分
        extract_section = ""
        lines = content.split('\n')
        
        in_extract_section = False
        for line in lines:
            if '提取所有个体孔位' in line:
                in_extract_section = True
            elif in_extract_section and line.strip() == '':
                break
            
            if in_extract_section:
                extract_section += line + '\n'
        
        # 检查是否简化为单一循环
        if 'for unit in self.detection_units:' in extract_section:
            if 'self.snake_sorted_holes.extend(unit.holes)' in extract_section:
                if 'if hasattr(' not in extract_section and 'isinstance(' not in extract_section:
                    logger.info("   ✅ 孔位提取逻辑已简化为单一循环")
                    return True
                else:
                    logger.warning("   ⚠️ 孔位提取仍有复杂分支")
                    return False
        
        logger.warning("   ⚠️ 孔位提取逻辑未找到或格式不符")
        return False
        
    except Exception as e:
        logger.error(f"   ❌ 孔位提取测试失败: {e}")
        return False

def test_color_override_interface():
    """测试颜色覆盖接口"""
    logger.info("🎨 测试5: 颜色覆盖接口")
    
    try:
        with open('src/core_business/graphics/graphics_view.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查update_hole_status方法签名
        if 'def update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None):' in content:
            logger.info("   ✅ update_hole_status支持颜色覆盖")
        else:
            logger.error("   ❌ update_hole_status不支持颜色覆盖")
            return False
        
        # 检查set_hole_color_override方法
        if 'def set_hole_color_override(self, hole_id: str, color_override):' in content:
            logger.info("   ✅ set_hole_color_override方法存在")
        else:
            logger.error("   ❌ set_hole_color_override方法缺失")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"   ❌ 颜色覆盖接口测试失败: {e}")
        return False

def test_method_simplification():
    """测试方法简化"""
    logger.info("🔧 测试6: 方法简化")
    
    try:
        with open('src/pages/main_detection_p1/components/simulation_controller.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查检测启动是否简化
        if 'self._start_pair_detection(current_unit)' in content:
            # 确保没有复杂的分支
            if '# 开始检测：仅HolePair检测' in content:
                logger.info("   ✅ 检测启动逻辑已简化")
            else:
                logger.warning("   ⚠️ 检测启动逻辑可能未完全简化")
                return False
        else:
            logger.error("   ❌ 检测启动逻辑未找到")
            return False
            
        # 检查状态确定是否简化
        if '# 处理HolePair检测的最终状态' in content:
            logger.info("   ✅ 状态确定逻辑已简化")
        else:
            logger.warning("   ⚠️ 状态确定逻辑未简化")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"   ❌ 方法简化测试失败: {e}")
        return False

def run_unit_tests():
    """运行所有单元测试"""
    logger.info("🧪 开始修复验证单元测试")
    logger.info("=" * 50)
    
    tests = [
        ("定时器常量", test_timer_constants),
        ("后备模式删除", test_fallback_removal),
        ("类型检查简化", test_type_check_simplification),
        ("孔位提取逻辑", test_hole_extraction_logic),
        ("颜色覆盖接口", test_color_override_interface),
        ("方法简化", test_method_simplification),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"{test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 统计结果
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info("=" * 50)
    logger.info("📊 测试结果汇总:")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"   {test_name}: {status}")
    
    logger.info(f"\n🏆 总体结果: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有修复验证通过！")
        return True
    else:
        logger.warning(f"⚠️ 有 {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = run_unit_tests()
    sys.exit(0 if success else 1)