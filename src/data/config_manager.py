"""
配置管理器模块
提供统一的配置管理功能
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from threading import Lock

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self._config: Dict[str, Any] = {}
        self._lock = Lock()
        
        # 默认配置文件路径
        if config_file is None:
            config_file = "config/config.json"
        
        self.config_file = Path(config_file)
        self._load_config()
        self._set_default_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self.logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                self.logger.warning(f"配置文件不存在: {self.config_file}")
                self._config = {}
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {e}")
            self._config = {}
    
    def _set_default_config(self):
        """设置默认配置"""
        defaults = {
            'app_name': 'AIDCIS3-LFS',
            'version': '2.0.0',
            'debug': False,
            'log_level': 'INFO',
            'database': {
                'url': 'sqlite:///detection_system.db',
                'echo': False
            },
            'ui': {
                'theme': 'dark',
                'font_size': 14,
                'window_size': [1400, 900]
            },
            'detection': {
                'model_path': 'models/yolo_v8.pt',
                'confidence_threshold': 0.6,
                'nms_threshold': 0.4
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_path': 'logs/aidcis.log'
            },
            'performance': {
                'max_workers': 8,
                'cache_size': 2000
            },
            'paths': {
                'data_dir': 'Data',
                'assets_dir': 'assets',
                'temp_dir': 'temp_charts'
            }
        }
        
        # 只设置不存在的默认值
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
            elif isinstance(value, dict) and isinstance(self._config[key], dict):
                # 递归设置嵌套字典的默认值
                self._set_nested_defaults(self._config[key], value)
    
    def _set_nested_defaults(self, config_dict: Dict[str, Any], defaults: Dict[str, Any]):
        """递归设置嵌套字典的默认值"""
        for key, value in defaults.items():
            if key not in config_dict:
                config_dict[key] = value
            elif isinstance(value, dict) and isinstance(config_dict[key], dict):
                self._set_nested_defaults(config_dict[key], value)
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键
        
        Args:
            key: 配置键，支持 'database.url' 这样的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        with self._lock:
            try:
                keys = key.split('.')
                value = self._config
                
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default
                
                return value
            except Exception as e:
                self.logger.error(f"获取配置失败 {key}: {e}")
                return default
    
    def set_config(self, key: str, value: Any) -> None:
        """
        设置配置值，支持点号分隔的嵌套键
        
        Args:
            key: 配置键
            value: 配置值
        """
        with self._lock:
            try:
                keys = key.split('.')
                config = self._config
                
                # 导航到最后一级的父字典
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    elif not isinstance(config[k], dict):
                        config[k] = {}
                    config = config[k]
                
                # 设置最终值
                config[keys[-1]] = value
                self.logger.debug(f"配置设置: {key} = {value}")
                
            except Exception as e:
                self.logger.error(f"设置配置失败 {key}: {e}")
    
    def has_config(self, key: str) -> bool:
        """检查配置是否存在"""
        with self._lock:
            try:
                keys = key.split('.')
                value = self._config
                
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return False
                
                return True
            except Exception:
                return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        with self._lock:
            return self._config.copy()
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """批量更新配置"""
        with self._lock:
            self._config.update(config)
            self.logger.debug(f"批量更新配置: {len(config)} 项")
    
    def save_config(self) -> None:
        """保存配置到文件"""
        with self._lock:
            try:
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"配置保存成功: {self.config_file}")
            except Exception as e:
                self.logger.error(f"配置保存失败: {e}")
    
    def reload_config(self) -> None:
        """重新加载配置文件"""
        with self._lock:
            self._load_config()
            self._set_default_config()
            self.logger.info("配置重新加载完成")
    
    def get_config_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """根据前缀获取配置"""
        with self._lock:
            result = {}
            prefix_with_dot = f"{prefix}."
            
            def extract_nested(config_dict: Dict[str, Any], current_prefix: str = ""):
                for key, value in config_dict.items():
                    full_key = f"{current_prefix}.{key}" if current_prefix else key
                    
                    if full_key.startswith(prefix_with_dot):
                        # 移除前缀
                        result_key = full_key[len(prefix_with_dot):]
                        result[result_key] = value
                    elif full_key == prefix:
                        return value
                    elif isinstance(value, dict):
                        extract_nested(value, full_key)
            
            extract_nested(self._config)
            return result
    
    def add_change_callback(self, callback):
        """添加配置变更回调（兼容性方法）"""
        # 这里可以实现配置变更监听逻辑
        pass


# 创建全局配置管理器实例
config_manager = ConfigManager()

# 提供便捷的函数接口
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return config_manager.get_config(key, default)

def set_config(key: str, value: Any) -> None:
    """设置配置值的便捷函数"""
    config_manager.set_config(key, value)

def has_config(key: str) -> bool:
    """检查配置是否存在的便捷函数"""
    return config_manager.has_config(key)
