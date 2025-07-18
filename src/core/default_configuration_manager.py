"""
默认配置管理器实现
提供基本的配置管理功能以满足依赖注入需求
"""

import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

from .interfaces.service_interfaces import IConfigurationManager, ServiceStatus
from .dependency_injection import injectable, ServiceLifetime


@injectable(ServiceLifetime.SINGLETON)
class DefaultConfigurationManager(IConfigurationManager):
    """默认配置管理器实现"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(config_file) if config_file else None
        self._config: Dict[str, Any] = {}
        self._status = ServiceStatus.INACTIVE
        
        # 尝试加载配置文件
        if self.config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self.logger.info(f"配置文件加载成功: {self.config_file}")
            except Exception as e:
                self.logger.warning(f"配置文件加载失败: {e}")
                self._config = {}
        
        # 设置默认配置
        self._set_default_config()
        self._status = ServiceStatus.ACTIVE
    
    def _set_default_config(self):
        """设置默认配置"""
        defaults = {
            'app_name': 'AIDCIS3-LFS',
            'version': '2.0.0',
            'debug': False,
            'log_level': 'INFO',
            'database_url': 'sqlite:///aidcis3.db',
            'cache_enabled': True,
            'cache_ttl': 3600,
            'max_workers': 4,
            'timeout': 30,
            'error_recovery_enabled': True,
            'plugin_directory': 'plugins',
            'temp_directory': 'temp',
            'data_directory': 'data',
            'backup_directory': 'backups'
        }
        
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self._config[key] = value
        self.logger.debug(f"配置设置: {key} = {value}")
    
    def has(self, key: str) -> bool:
        """检查配置是否存在"""
        return key in self._config
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def update(self, config: Dict[str, Any]) -> None:
        """批量更新配置"""
        self._config.update(config)
        self.logger.debug(f"批量更新配置: {len(config)} 项")
    
    def remove(self, key: str) -> bool:
        """删除配置项"""
        if key in self._config:
            del self._config[key]
            self.logger.debug(f"配置删除: {key}")
            return True
        return False
    
    def save(self) -> bool:
        """保存配置到文件"""
        if not self.config_file:
            return False
        
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置保存成功: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"配置保存失败: {e}")
            return False
    
    def reload(self) -> bool:
        """重新加载配置文件"""
        if not self.config_file or not self.config_file.exists():
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                new_config = json.load(f)
            
            self._config = new_config
            self._set_default_config()  # 确保默认值存在
            self.logger.info(f"配置重新加载成功: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"配置重新加载失败: {e}")
            return False
    
    def get_status(self) -> ServiceStatus:
        """获取服务状态"""
        return self._status
    
    def is_healthy(self) -> bool:
        """检查服务健康状态"""
        return self._status == ServiceStatus.ACTIVE
    
    def start(self) -> None:
        """启动服务"""
        if self._status == ServiceStatus.INACTIVE:
            self._status = ServiceStatus.ACTIVE
            self.logger.info("配置管理器启动成功")
    
    def stop(self) -> None:
        """停止服务"""
        if self._status == ServiceStatus.ACTIVE:
            self._status = ServiceStatus.INACTIVE
            self.logger.info("配置管理器已停止")
    
    def load_from_file(self, file_path: str) -> None:
        """从文件加载配置"""
        try:
            config_path = Path(file_path)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    new_config = json.load(f)
                self._config.update(new_config)
                self.logger.info(f"从文件加载配置成功: {file_path}")
            else:
                self.logger.warning(f"配置文件不存在: {file_path}")
        except Exception as e:
            self.logger.error(f"从文件加载配置失败: {e}")
    
    def save_to_file(self, file_path: str) -> None:
        """保存配置到文件"""
        try:
            config_path = Path(file_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"保存配置到文件成功: {file_path}")
        except Exception as e:
            self.logger.error(f"保存配置到文件失败: {e}")
    
    def __str__(self) -> str:
        return f"DefaultConfigurationManager(status={self._status.value}, config_count={len(self._config)})"