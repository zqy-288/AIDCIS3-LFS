"""
全局旋转配置管理器
统一管理项目中所有旋转相关的配置
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class RotationDirection(Enum):
    """旋转方向"""
    CLOCKWISE = "clockwise"           # 顺时针
    COUNTER_CLOCKWISE = "counter_clockwise"  # 逆时针


@dataclass
class GlobalRotationConfig:
    """全局旋转配置 - 已禁用所有旋转功能"""
    enabled: bool = False  # 全局禁用旋转
    angle: float = 0.0  # 旋转角度设为0
    direction: RotationDirection = RotationDirection.CLOCKWISE
    
    # 各组件旋转启用控制 - 全部禁用
    enable_coordinate_rotation: bool = False     # 坐标系旋转 - 已禁用
    enable_view_transform_rotation: bool = False  # 视图变换旋转 - 已禁用
    enable_scale_manager_rotation: bool = False   # 缩放管理器旋转 - 已禁用
    enable_dynamic_sector_rotation: bool = False  # 动态扇形旋转 - 已禁用
    
    # 调试选项
    debug_enabled: bool = True  # 保持调试功能


class GlobalRotationManager:
    """全局旋转管理器 - 单例模式"""
    
    _instance: Optional['GlobalRotationManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'GlobalRotationManager':
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化全局旋转管理器"""
        if self._initialized:
            return
            
        # 加载默认配置
        self._config = GlobalRotationConfig()
        self._load_config_from_settings()
        self._initialized = True
        
        if self._config.debug_enabled:
            print(f"🔄 [全局旋转] 初始化完成: {self._config.angle}°{self._config.direction.value}")
    
    def _load_config_from_settings(self):
        """从配置文件加载旋转设置"""
        try:
            from src.data.config_manager import get_config
            
            # 主旋转配置
            self._config.enabled = get_config('rotation.global.enabled', True)
            self._config.angle = get_config('rotation.global.angle', 90.0)
            direction_str = get_config('rotation.global.direction', 'clockwise')
            
            # 转换方向枚举
            if direction_str == 'counter_clockwise':
                self._config.direction = RotationDirection.COUNTER_CLOCKWISE
            else:
                self._config.direction = RotationDirection.CLOCKWISE
            
            # 各组件启用控制
            self._config.enable_coordinate_rotation = get_config('rotation.coordinate.enabled', True)
            self._config.enable_view_transform_rotation = get_config('rotation.view_transform.enabled', True)
            self._config.enable_scale_manager_rotation = get_config('rotation.scale_manager.enabled', True)
            self._config.enable_dynamic_sector_rotation = get_config('rotation.dynamic_sector.enabled', True)
            
            # 调试配置 - 临时启用以诊断问题
            self._config.debug_enabled = get_config('rotation.debug.enabled', True)
            
        except Exception as e:
            print(f"⚠️ [全局旋转] 配置加载失败，使用默认值: {e}")
    
    @property
    def config(self) -> GlobalRotationConfig:
        """获取旋转配置"""
        return self._config
    
    def get_rotation_angle(self, component: str = "default") -> float:
        """
        获取指定组件的旋转角度 - 已禁用，始终返回0
        
        Args:
            component: 组件名称 ("coordinate", "view_transform", "scale_manager", "dynamic_sector")
        
        Returns:
            旋转角度（度） - 已禁用，始终返回0
        """
        # 所有旋转功能已禁用，始终返回0
        if self._config.debug_enabled:
            print(f"🔄 [全局旋转] {component}组件旋转已禁用: 0°")
        
        return 0.0
    
    def is_rotation_enabled(self, component: str = "default") -> bool:
        """
        检查指定组件是否启用旋转 - 已禁用，始终返回False
        
        Args:
            component: 组件名称
            
        Returns:
            是否启用旋转 - 已禁用，始终返回False
        """
        # 所有旋转功能已禁用，始终返回False
        return False
    
    def get_rotation_matrix_params(self, component: str = "default") -> Dict[str, float]:
        """
        获取旋转矩阵参数 - 已禁用，始终返回无旋转矩阵
        
        Returns:
            包含cos和sin值的字典 - 无旋转状态
        """
        # 旋转已禁用，返回单位矩阵参数（无旋转）
        return {'cos': 1.0, 'sin': 0.0, 'angle_rad': 0.0, 'angle_deg': 0.0}
    
    def update_config(self, **kwargs):
        """
        更新旋转配置
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
                if self._config.debug_enabled:
                    print(f"🔄 [全局旋转] 配置更新: {key} = {value}")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """获取调试信息"""
        return {
            'enabled': self._config.enabled,
            'angle': self._config.angle,
            'direction': self._config.direction.value,
            'components': {
                'coordinate': self._config.enable_coordinate_rotation,
                'view_transform': self._config.enable_view_transform_rotation,
                'scale_manager': self._config.enable_scale_manager_rotation,
                'dynamic_sector': self._config.enable_dynamic_sector_rotation,
            },
            'debug_enabled': self._config.debug_enabled
        }


# 全局实例
_rotation_manager = None


def get_rotation_manager() -> GlobalRotationManager:
    """获取全局旋转管理器实例"""
    global _rotation_manager
    if _rotation_manager is None:
        _rotation_manager = GlobalRotationManager()
    return _rotation_manager


def get_rotation_angle(component: str = "default") -> float:
    """快捷函数：获取旋转角度"""
    return get_rotation_manager().get_rotation_angle(component)


def is_rotation_enabled(component: str = "default") -> bool:
    """快捷函数：检查是否启用旋转"""
    return get_rotation_manager().is_rotation_enabled(component)