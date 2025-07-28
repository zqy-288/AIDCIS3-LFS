"""
全局旋转控制工具函数
提供便捷的旋转控制接口
"""

from typing import Dict, Any
from src.core_business.graphics.rotation_config import get_rotation_manager


# 已禁用所有旋转功能
def set_global_rotation_enabled(enabled: bool):
    """
    全局启用/禁用所有旋转功能 - 已禁用，无效操作
    
    Args:
        enabled: 是否启用旋转 - 忽略，功能已禁用
    """
    # 旋转功能已全局禁用，不执行任何操作
    print(f"🔄 [全局旋转控制] 旋转功能已全局禁用，操作无效")


# 已禁用所有旋转功能
def set_rotation_angle(angle: float, direction: str = "clockwise"):
    """
    设置全局旋转角度和方向 - 已禁用，无效操作
    
    Args:
        angle: 旋转角度（度） - 忽略，功能已禁用
        direction: 旋转方向 - 忽略，功能已禁用
    """
    # 旋转功能已全局禁用，不执行任何操作
    print(f"🔄 [全局旋转控制] 旋转功能已全局禁用，角度设置无效: {angle}°")


# 已禁用所有旋转功能
def toggle_component_rotation(component: str, enabled: bool = None):
    """
    切换指定组件的旋转功能 - 已禁用，无效操作
    
    Args:
        component: 组件名称 - 忽略，功能已禁用
        enabled: 是否启用 - 忽略，功能已禁用
    """
    # 旋转功能已全局禁用，不执行任何操作
    print(f"🔄 [全局旋转控制] 旋转功能已全局禁用，{component}组件操作无效")


def get_rotation_status() -> Dict[str, Any]:
    """
    获取当前旋转状态信息
    
    Returns:
        旋转状态字典
    """
    manager = get_rotation_manager()
    return manager.get_debug_info()


def print_rotation_status():
    """打印当前旋转状态"""
    status = get_rotation_status()
    print("🔄 [全局旋转状态]")
    print(f"   全局启用: {status['enabled']}")
    print(f"   旋转角度: {status['angle']}°")
    print(f"   旋转方向: {status['direction']}")
    print(f"   组件状态:")
    for component, enabled in status['components'].items():
        print(f"     {component}: {'✅' if enabled else '❌'}")


# 已禁用所有旋转功能
def reset_rotation_to_defaults():
    """重置旋转配置为默认值 - 已禁用，无效操作"""
    # 旋转功能已全局禁用，不执行任何操作
    print("🔄 [全局旋转控制] 旋转功能已全局禁用，重置操作无效")


# 快捷控制函数 - 已禁用所有旋转功能
def disable_all_rotation():
    """禁用所有旋转 - 已禁用，无效操作"""
    print("🔄 [全局旋转控制] 旋转已全局禁用")


def enable_all_rotation():
    """启用所有旋转 - 已禁用，无效操作"""
    print("🔄 [全局旋转控制] 旋转功能已全局禁用，启用操作无效")


def set_clockwise_90():
    """设置为顺时针90度旋转 - 已禁用，无效操作"""
    print("🔄 [全局旋转控制] 旋转功能已全局禁用，角度设置无效")


def set_counter_clockwise_90():
    """设置为逆时针90度旋转 - 已禁用，无效操作"""
    print("🔄 [全局旋转控制] 旋转功能已全局禁用，角度设置无效")


if __name__ == "__main__":
    # 测试脚本 - 旋转功能已禁用
    print("🚀 全局旋转控制测试 - 旋转功能已禁用")
    print_rotation_status()
    print("\n测试设置旋转（已禁用）...")
    set_clockwise_90()
    print_rotation_status()