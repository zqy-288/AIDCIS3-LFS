"""
插件配置和元数据支持系统
提供插件配置管理、验证、热重载等功能
"""

import json
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Type, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging
import jsonschema
from jsonschema import ValidationError
import yaml

from .plugin_manager import PluginMetadata
from .interfaces.service_interfaces import IConfigurationManager
from .application import ApplicationEvent, EventBus


class ConfigFormat(Enum):
    """配置文件格式"""
    JSON = "json"
    YAML = "yaml"
    INI = "ini"
    TOML = "toml"


class ConfigScope(Enum):
    """配置作用域"""
    GLOBAL = "global"
    PLUGIN = "plugin"
    USER = "user"
    ENVIRONMENT = "environment"


@dataclass
class ConfigSchema:
    """配置模式定义"""
    name: str
    version: str
    schema: Dict[str, Any]
    description: str = ""
    required_fields: List[str] = field(default_factory=list)
    default_values: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置"""
        try:
            jsonschema.validate(config, self.schema)
            return True
        except ValidationError:
            return False
    
    def get_validation_errors(self, config: Dict[str, Any]) -> List[str]:
        """获取验证错误列表"""
        errors = []
        try:
            jsonschema.validate(config, self.schema)
        except ValidationError as e:
            errors.append(str(e))
        
        # 检查必填字段
        for field in self.required_fields:
            if field not in config:
                errors.append(f"Required field '{field}' is missing")
        
        return errors


@dataclass
class ConfigEntry:
    """配置条目"""
    key: str
    value: Any
    scope: ConfigScope
    source: str  # 配置来源文件或环境变量
    timestamp: float = field(default_factory=time.time)
    description: str = ""
    is_encrypted: bool = False
    is_readonly: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'key': self.key,
            'value': self.value,
            'scope': self.scope.value,
            'source': self.source,
            'timestamp': self.timestamp,
            'description': self.description,
            'is_encrypted': self.is_encrypted,
            'is_readonly': self.is_readonly
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigEntry':
        """从字典创建"""
        return cls(
            key=data['key'],
            value=data['value'],
            scope=ConfigScope(data.get('scope', 'plugin')),
            source=data.get('source', ''),
            timestamp=data.get('timestamp', time.time()),
            description=data.get('description', ''),
            is_encrypted=data.get('is_encrypted', False),
            is_readonly=data.get('is_readonly', False)
        )


class IConfigurationProvider(ABC):
    """配置提供器接口"""
    
    @abstractmethod
    def load_config(self, source: str) -> Dict[str, Any]:
        """加载配置"""
        pass
    
    @abstractmethod
    def save_config(self, config: Dict[str, Any], target: str) -> bool:
        """保存配置"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[ConfigFormat]:
        """获取支持的格式"""
        pass
    
    @abstractmethod
    def can_handle(self, source: str) -> bool:
        """检查是否可以处理指定源"""
        pass


class JsonConfigProvider(IConfigurationProvider):
    """JSON配置提供器"""
    
    def load_config(self, source: str) -> Dict[str, Any]:
        """加载JSON配置"""
        try:
            with open(source, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load JSON config from {source}: {e}")
    
    def save_config(self, config: Dict[str, Any], target: str) -> bool:
        """保存JSON配置"""
        try:
            with open(target, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[ConfigFormat]:
        """支持的格式"""
        return [ConfigFormat.JSON]
    
    def can_handle(self, source: str) -> bool:
        """检查是否可以处理"""
        return source.endswith('.json')


class YamlConfigProvider(IConfigurationProvider):
    """YAML配置提供器"""
    
    def load_config(self, source: str) -> Dict[str, Any]:
        """加载YAML配置"""
        try:
            with open(source, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise RuntimeError(f"Failed to load YAML config from {source}: {e}")
    
    def save_config(self, config: Dict[str, Any], target: str) -> bool:
        """保存YAML配置"""
        try:
            with open(target, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[ConfigFormat]:
        """支持的格式"""
        return [ConfigFormat.YAML]
    
    def can_handle(self, source: str) -> bool:
        """检查是否可以处理"""
        return source.endswith(('.yaml', '.yml'))


class EnvironmentConfigProvider(IConfigurationProvider):
    """环境变量配置提供器"""
    
    def __init__(self, prefix: str = "AIDCIS_"):
        self.prefix = prefix
    
    def load_config(self, source: str = "") -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = {}
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                # 移除前缀并转换为配置键
                config_key = key[len(self.prefix):].lower().replace('_', '.')
                config[config_key] = self._convert_value(value)
        return config
    
    def save_config(self, config: Dict[str, Any], target: str = "") -> bool:
        """环境变量不支持保存"""
        return False
    
    def get_supported_formats(self) -> List[ConfigFormat]:
        """支持的格式"""
        return []
    
    def can_handle(self, source: str) -> bool:
        """总是可以处理环境变量"""
        return source == "environment" or source == ""
    
    def _convert_value(self, value: str) -> Any:
        """转换环境变量值"""
        # 尝试转换为适当的类型
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value


class PluginConfigurationManager:
    """插件配置管理器"""
    
    def __init__(self, 
                 base_config_manager: Optional[IConfigurationManager] = None,
                 event_bus: Optional[EventBus] = None,
                 logger: Optional[logging.Logger] = None):
        self._base_config_manager = base_config_manager
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)
        
        # 配置存储
        self._configs: Dict[str, Dict[str, ConfigEntry]] = {}  # plugin_id -> {key -> ConfigEntry}
        self._schemas: Dict[str, ConfigSchema] = {}  # plugin_id -> ConfigSchema
        self._global_config: Dict[str, ConfigEntry] = {}
        
        # 配置提供器
        self._providers: List[IConfigurationProvider] = []
        self._register_default_providers()
        
        # 配置文件监控
        self._config_files: Dict[str, float] = {}  # file_path -> last_modified
        self._watchers: Dict[str, Callable] = {}  # plugin_id -> callback
        
        # 变更通知
        self._change_callbacks: List[Callable[[str, str, Any, Any], None]] = []
        
        if self._logger:
            self._logger.info("PluginConfigurationManager initialized")
    
    def _register_default_providers(self):
        """注册默认的配置提供器"""
        self.add_provider(JsonConfigProvider())
        self.add_provider(YamlConfigProvider())
        self.add_provider(EnvironmentConfigProvider())
    
    def add_provider(self, provider: IConfigurationProvider):
        """添加配置提供器"""
        self._providers.append(provider)
        if self._logger:
            self._logger.debug(f"Added config provider: {provider.__class__.__name__}")
    
    def register_plugin_schema(self, plugin_id: str, schema: ConfigSchema):
        """注册插件配置模式"""
        self._schemas[plugin_id] = schema
        
        # 确保插件配置存储存在
        if plugin_id not in self._configs:
            self._configs[plugin_id] = {}
        
        # 应用默认值
        for key, default_value in schema.default_values.items():
            if key not in self._configs[plugin_id]:
                entry = ConfigEntry(
                    key=key,
                    value=default_value,
                    scope=ConfigScope.PLUGIN,
                    source="default",
                    description=f"Default value for {key}"
                )
                self._configs[plugin_id][key] = entry
        
        if self._logger:
            self._logger.info(f"Registered config schema for plugin: {plugin_id}")
    
    def load_plugin_config(self, plugin_id: str, config_file: Optional[str] = None) -> bool:
        """加载插件配置"""
        try:
            # 确保插件配置存储存在
            if plugin_id not in self._configs:
                self._configs[plugin_id] = {}
            
            config_data = {}
            
            # 1. 从指定配置文件加载
            if config_file and os.path.exists(config_file):
                config_data.update(self._load_config_from_file(config_file))
                self._config_files[config_file] = os.path.getmtime(config_file)
            
            # 2. 从基础配置管理器加载插件特定配置
            if self._base_config_manager:
                plugin_config = self._base_config_manager.get(f'plugin.{plugin_id}', {})
                if isinstance(plugin_config, dict):
                    config_data.update(plugin_config)
            
            # 3. 从环境变量加载
            env_provider = next((p for p in self._providers if isinstance(p, EnvironmentConfigProvider)), None)
            if env_provider:
                env_config = env_provider.load_config()
                # 过滤插件相关的环境变量
                plugin_env_config = {k: v for k, v in env_config.items() if k.startswith(f'plugin.{plugin_id}.')}
                config_data.update(plugin_env_config)
            
            # 验证配置
            if plugin_id in self._schemas:
                schema = self._schemas[plugin_id]
                if not schema.validate(config_data):
                    errors = schema.get_validation_errors(config_data)
                    if self._logger:
                        self._logger.warning(f"Config validation failed for {plugin_id}: {errors}")
            
            # 存储配置条目
            for key, value in config_data.items():
                source = config_file or "base_config"
                entry = ConfigEntry(
                    key=key,
                    value=value,
                    scope=ConfigScope.PLUGIN,
                    source=source,
                    description=f"Configuration for {plugin_id}.{key}"
                )
                
                # 检查是否有变更
                old_value = None
                if key in self._configs[plugin_id]:
                    old_value = self._configs[plugin_id][key].value
                
                self._configs[plugin_id][key] = entry
                
                # 通知变更
                if old_value != value:
                    self._notify_config_change(plugin_id, key, old_value, value)
            
            if self._logger:
                self._logger.info(f"Loaded config for plugin {plugin_id}: {len(config_data)} entries")
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to load config for plugin {plugin_id}: {e}")
            return False
    
    def _load_config_from_file(self, config_file: str) -> Dict[str, Any]:
        """从文件加载配置"""
        for provider in self._providers:
            if provider.can_handle(config_file):
                return provider.load_config(config_file)
        
        raise RuntimeError(f"No provider found for config file: {config_file}")
    
    def save_plugin_config(self, plugin_id: str, config_file: Optional[str] = None) -> bool:
        """保存插件配置"""
        try:
            if plugin_id not in self._configs:
                return False
            
            # 构建配置数据
            config_data = {}
            for entry in self._configs[plugin_id].values():
                if not entry.is_readonly:
                    config_data[entry.key] = entry.value
            
            # 确定保存位置
            if not config_file:
                config_file = f"configs/{plugin_id}.json"
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # 查找合适的提供器
            for provider in self._providers:
                if provider.can_handle(config_file):
                    if provider.save_config(config_data, config_file):
                        self._config_files[config_file] = os.path.getmtime(config_file)
                        if self._logger:
                            self._logger.info(f"Saved config for plugin {plugin_id} to {config_file}")
                        return True
            
            return False
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to save config for plugin {plugin_id}: {e}")
            return False
    
    def get_plugin_config(self, plugin_id: str, key: str = None) -> Any:
        """获取插件配置"""
        if plugin_id not in self._configs:
            return None if key else {}
        
        if key:
            entry = self._configs[plugin_id].get(key)
            return entry.value if entry else None
        else:
            return {k: v.value for k, v in self._configs[plugin_id].items()}
    
    def set_plugin_config(self, plugin_id: str, key: str, value: Any, 
                         source: str = "manual", persist: bool = True) -> bool:
        """设置插件配置"""
        try:
            # 确保插件配置存储存在
            if plugin_id not in self._configs:
                self._configs[plugin_id] = {}
            
            # 获取旧值
            old_value = None
            if key in self._configs[plugin_id]:
                old_entry = self._configs[plugin_id][key]
                if old_entry.is_readonly:
                    if self._logger:
                        self._logger.warning(f"Cannot modify readonly config {plugin_id}.{key}")
                    return False
                old_value = old_entry.value
            
            # 验证配置
            if plugin_id in self._schemas:
                schema = self._schemas[plugin_id]
                temp_config = self.get_plugin_config(plugin_id) or {}
                temp_config[key] = value
                
                if not schema.validate(temp_config):
                    errors = schema.get_validation_errors(temp_config)
                    if self._logger:
                        self._logger.error(f"Config validation failed for {plugin_id}.{key}: {errors}")
                    return False
            
            # 创建配置条目
            entry = ConfigEntry(
                key=key,
                value=value,
                scope=ConfigScope.PLUGIN,
                source=source,
                description=f"Configuration for {plugin_id}.{key}"
            )
            
            self._configs[plugin_id][key] = entry
            
            # 同步到基础配置管理器
            if self._base_config_manager:
                self._base_config_manager.set(f'plugin.{plugin_id}.{key}', value)
            
            # 持久化
            if persist:
                self.save_plugin_config(plugin_id)
            
            # 通知变更
            if old_value != value:
                self._notify_config_change(plugin_id, key, old_value, value)
            
            if self._logger:
                self._logger.debug(f"Set config {plugin_id}.{key} = {value}")
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to set config {plugin_id}.{key}: {e}")
            return False
    
    def get_config_schema(self, plugin_id: str) -> Optional[ConfigSchema]:
        """获取插件配置模式"""
        return self._schemas.get(plugin_id)
    
    def validate_plugin_config(self, plugin_id: str) -> Tuple[bool, List[str]]:
        """验证插件配置"""
        if plugin_id not in self._schemas:
            return True, []
        
        schema = self._schemas[plugin_id]
        config = self.get_plugin_config(plugin_id) or {}
        
        errors = schema.get_validation_errors(config)
        return len(errors) == 0, errors
    
    def reload_plugin_config(self, plugin_id: str) -> bool:
        """重新加载插件配置"""
        # 查找配置文件
        config_file = None
        for file_path in self._config_files:
            if plugin_id in file_path:
                config_file = file_path
                break
        
        return self.load_plugin_config(plugin_id, config_file)
    
    def watch_config_changes(self, plugin_id: str, callback: Callable[[str, Any, Any], None]):
        """监控配置变更"""
        self._watchers[plugin_id] = callback
        if self._logger:
            self._logger.debug(f"Added config watcher for plugin: {plugin_id}")
    
    def unwatch_config_changes(self, plugin_id: str):
        """取消监控配置变更"""
        self._watchers.pop(plugin_id, None)
    
    def check_config_file_changes(self):
        """检查配置文件变更"""
        for file_path, last_modified in list(self._config_files.items()):
            try:
                if os.path.exists(file_path):
                    current_modified = os.path.getmtime(file_path)
                    if current_modified > last_modified:
                        # 文件已被修改，重新加载配置
                        plugin_id = self._extract_plugin_id_from_path(file_path)
                        if plugin_id:
                            if self._logger:
                                self._logger.info(f"Config file changed, reloading: {file_path}")
                            self.reload_plugin_config(plugin_id)
                            self._config_files[file_path] = current_modified
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error checking config file {file_path}: {e}")
    
    def _extract_plugin_id_from_path(self, file_path: str) -> Optional[str]:
        """从文件路径提取插件ID"""
        # 简单实现：从文件名中提取
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        return name_without_ext if name_without_ext in self._configs else None
    
    def _notify_config_change(self, plugin_id: str, key: str, old_value: Any, new_value: Any):
        """通知配置变更"""
        # 通知插件特定的监听器
        if plugin_id in self._watchers:
            try:
                self._watchers[plugin_id](key, old_value, new_value)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Config watcher error for {plugin_id}: {e}")
        
        # 通知全局变更回调
        for callback in self._change_callbacks:
            try:
                callback(plugin_id, key, old_value, new_value)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Config change callback error: {e}")
        
        # 发布事件
        if self._event_bus:
            event = ApplicationEvent("plugin_config_changed", {
                "plugin_id": plugin_id,
                "key": key,
                "old_value": old_value,
                "new_value": new_value
            })
            self._event_bus.post_event(event)
    
    def add_change_callback(self, callback: Callable[[str, str, Any, Any], None]):
        """添加配置变更回调"""
        self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[str, str, Any, Any], None]):
        """移除配置变更回调"""
        try:
            self._change_callbacks.remove(callback)
        except ValueError:
            pass
    
    # 全局配置管理
    def set_global_config(self, key: str, value: Any, source: str = "manual") -> bool:
        """设置全局配置"""
        try:
            old_value = None
            if key in self._global_config:
                old_value = self._global_config[key].value
            
            entry = ConfigEntry(
                key=key,
                value=value,
                scope=ConfigScope.GLOBAL,
                source=source,
                description=f"Global configuration for {key}"
            )
            
            self._global_config[key] = entry
            
            # 同步到基础配置管理器
            if self._base_config_manager:
                self._base_config_manager.set(f'global.{key}', value)
            
            # 通知变更
            if old_value != value:
                self._notify_config_change("global", key, old_value, value)
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to set global config {key}: {e}")
            return False
    
    def get_global_config(self, key: str = None) -> Any:
        """获取全局配置"""
        if key:
            entry = self._global_config.get(key)
            return entry.value if entry else None
        else:
            return {k: v.value for k, v in self._global_config.items()}
    
    # 配置导出和导入
    def export_plugin_config(self, plugin_id: str, format: ConfigFormat = ConfigFormat.JSON) -> Optional[str]:
        """导出插件配置"""
        try:
            if plugin_id not in self._configs:
                return None
            
            config_data = {}
            for key, entry in self._configs[plugin_id].items():
                config_data[key] = {
                    'value': entry.value,
                    'description': entry.description,
                    'source': entry.source,
                    'timestamp': entry.timestamp
                }
            
            if format == ConfigFormat.JSON:
                return json.dumps(config_data, indent=2, ensure_ascii=False)
            elif format == ConfigFormat.YAML:
                return yaml.dump(config_data, default_flow_style=False, allow_unicode=True)
            else:
                return str(config_data)
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to export config for {plugin_id}: {e}")
            return None
    
    def import_plugin_config(self, plugin_id: str, config_data: str, 
                           format: ConfigFormat = ConfigFormat.JSON) -> bool:
        """导入插件配置"""
        try:
            if format == ConfigFormat.JSON:
                data = json.loads(config_data)
            elif format == ConfigFormat.YAML:
                data = yaml.safe_load(config_data)
            else:
                return False
            
            for key, entry_data in data.items():
                if isinstance(entry_data, dict) and 'value' in entry_data:
                    self.set_plugin_config(plugin_id, key, entry_data['value'], 
                                         entry_data.get('source', 'import'), persist=False)
                else:
                    self.set_plugin_config(plugin_id, key, entry_data, 'import', persist=False)
            
            # 保存配置
            self.save_plugin_config(plugin_id)
            
            if self._logger:
                self._logger.info(f"Imported config for plugin {plugin_id}")
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to import config for {plugin_id}: {e}")
            return False
    
    # 统计和查询
    def get_config_statistics(self) -> Dict[str, Any]:
        """获取配置统计信息"""
        stats = {
            'total_plugins': len(self._configs),
            'total_global_configs': len(self._global_config),
            'total_schemas': len(self._schemas),
            'config_files_monitored': len(self._config_files),
            'active_watchers': len(self._watchers),
            'config_providers': len(self._providers)
        }
        
        # 按作用域统计
        scope_stats = {}
        for scope in ConfigScope:
            scope_stats[scope.value] = 0
        
        for plugin_configs in self._configs.values():
            for entry in plugin_configs.values():
                scope_stats[entry.scope.value] += 1
        
        for entry in self._global_config.values():
            scope_stats[entry.scope.value] += 1
        
        stats['by_scope'] = scope_stats
        
        return stats
    
    def get_plugin_config_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """获取插件配置信息"""
        if plugin_id not in self._configs:
            return None
        
        config_entries = []
        for entry in self._configs[plugin_id].values():
            config_entries.append(entry.to_dict())
        
        info = {
            'plugin_id': plugin_id,
            'config_count': len(config_entries),
            'config_entries': config_entries,
            'has_schema': plugin_id in self._schemas,
            'has_watcher': plugin_id in self._watchers
        }
        
        if plugin_id in self._schemas:
            schema = self._schemas[plugin_id]
            is_valid, errors = self.validate_plugin_config(plugin_id)
            info['schema_info'] = {
                'name': schema.name,
                'version': schema.version,
                'description': schema.description,
                'required_fields': schema.required_fields,
                'is_valid': is_valid,
                'validation_errors': errors
            }
        
        return info


# 便捷函数
def create_plugin_config_manager(base_config_manager: Optional[IConfigurationManager] = None,
                                event_bus: Optional[EventBus] = None,
                                logger: Optional[logging.Logger] = None) -> PluginConfigurationManager:
    """创建插件配置管理器"""
    return PluginConfigurationManager(base_config_manager, event_bus, logger)


def create_config_schema(name: str, version: str, schema: Dict[str, Any], 
                        description: str = "", required_fields: List[str] = None,
                        default_values: Dict[str, Any] = None) -> ConfigSchema:
    """创建配置模式"""
    return ConfigSchema(
        name=name,
        version=version,
        schema=schema,
        description=description,
        required_fields=required_fields or [],
        default_values=default_values or {}
    )