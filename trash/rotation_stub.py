"""
旋转功能存根 - 替换已删除的rotation_config
所有旋转功能已被禁用，此文件提供兼容性支持
"""


class DisabledRotationManager:
    """禁用的旋转管理器 - 提供兼容性接口"""
    
    def is_rotation_enabled(self, component_type: str = None) -> bool:
        """旋转是否启用 - 始终返回False"""
        return False
    
    def get_rotation_angle(self, component_type: str = None) -> float:
        """获取旋转角度 - 始终返回0.0"""
        return 0.0
    
    def is_debug_enabled(self) -> bool:
        """调试是否启用"""
        return False


# 全局禁用的旋转管理器实例
_disabled_manager = DisabledRotationManager()


def get_rotation_manager():
    """获取旋转管理器 - 返回禁用的管理器"""
    return _disabled_manager