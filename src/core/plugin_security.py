"""
插件安全和沙箱隔离系统
提供插件的安全执行环境、权限控制、版本兼容性检查等功能
"""

import os
import sys
import ast
import re
import importlib
import importlib.util
import subprocess
import threading
import time
import tempfile
import shutil
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Callable, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging
import weakref
import pickle
import json

from .plugin_manager import PluginMetadata


class SecurityLevel(Enum):
    """安全级别"""
    UNRESTRICTED = "unrestricted"  # 无限制
    RESTRICTED = "restricted"      # 受限制
    SANDBOXED = "sandboxed"       # 沙箱模式
    ISOLATED = "isolated"         # 完全隔离


class PermissionType(Enum):
    """权限类型"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    NETWORK_ACCESS = "network_access"
    SYSTEM_COMMAND = "system_command"
    MODULE_IMPORT = "module_import"
    DATABASE_ACCESS = "database_access"
    UI_MODIFICATION = "ui_modification"
    CONFIGURATION_ACCESS = "configuration_access"
    PLUGIN_COMMUNICATION = "plugin_communication"
    SYSTEM_INFORMATION = "system_information"


@dataclass
class SecurityPolicy:
    """安全策略"""
    level: SecurityLevel = SecurityLevel.RESTRICTED
    allowed_permissions: Set[PermissionType] = field(default_factory=set)
    allowed_modules: Set[str] = field(default_factory=set)
    allowed_paths: Set[str] = field(default_factory=set)
    blocked_functions: Set[str] = field(default_factory=set)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    execution_timeout: float = 30.0
    memory_limit: int = 128 * 1024 * 1024  # 128MB
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'level': self.level.value,
            'allowed_permissions': [p.value for p in self.allowed_permissions],
            'allowed_modules': list(self.allowed_modules),
            'allowed_paths': list(self.allowed_paths),
            'blocked_functions': list(self.blocked_functions),
            'resource_limits': self.resource_limits,
            'execution_timeout': self.execution_timeout,
            'memory_limit': self.memory_limit
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityPolicy':
        """从字典创建安全策略"""
        return cls(
            level=SecurityLevel(data.get('level', 'restricted')),
            allowed_permissions={PermissionType(p) for p in data.get('allowed_permissions', [])},
            allowed_modules=set(data.get('allowed_modules', [])),
            allowed_paths=set(data.get('allowed_paths', [])),
            blocked_functions=set(data.get('blocked_functions', [])),
            resource_limits=data.get('resource_limits', {}),
            execution_timeout=data.get('execution_timeout', 30.0),
            memory_limit=data.get('memory_limit', 128 * 1024 * 1024)
        )


@dataclass
class SecurityViolation:
    """安全违规记录"""
    plugin_id: str
    violation_type: str
    description: str
    severity: str
    timestamp: float = field(default_factory=time.time)
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'plugin_id': self.plugin_id,
            'violation_type': self.violation_type,
            'description': self.description,
            'severity': self.severity,
            'timestamp': self.timestamp,
            'stack_trace': self.stack_trace,
            'metadata': self.metadata
        }


class VersionManager:
    """版本管理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._app_version = "1.0.0"  # 应用程序版本
        self._api_version = "1.0.0"  # API版本
        
    def set_app_version(self, version: str):
        """设置应用程序版本"""
        self._app_version = version
    
    def set_api_version(self, version: str):
        """设置API版本"""
        self._api_version = version
    
    def check_compatibility(self, metadata: PluginMetadata) -> Tuple[bool, str]:
        """检查版本兼容性"""
        try:
            # 检查最低应用版本要求
            if not self._is_version_compatible(self._app_version, metadata.min_app_version, ">="):
                return False, f"应用版本过低，需要 >= {metadata.min_app_version}，当前版本: {self._app_version}"
            
            # 检查最高应用版本限制
            if metadata.max_app_version and not self._is_version_compatible(self._app_version, metadata.max_app_version, "<="):
                return False, f"应用版本过高，需要 <= {metadata.max_app_version}，当前版本: {self._app_version}"
            
            # 检查API版本兼容性
            if not self._is_api_compatible(metadata.api_version):
                return False, f"API版本不兼容，插件API: {metadata.api_version}，应用API: {self._api_version}"
            
            return True, "版本兼容"
            
        except Exception as e:
            self._logger.error(f"版本兼容性检查失败: {e}")
            return False, f"版本检查失败: {e}"
    
    def _is_version_compatible(self, current: str, required: str, operator: str) -> bool:
        """检查版本兼容性"""
        try:
            current_parts = [int(x) for x in current.split('.')]
            required_parts = [int(x) for x in required.split('.')]
            
            # 补齐版本号长度
            max_len = max(len(current_parts), len(required_parts))
            current_parts += [0] * (max_len - len(current_parts))
            required_parts += [0] * (max_len - len(required_parts))
            
            if operator == ">=":
                return current_parts >= required_parts
            elif operator == "<=":
                return current_parts <= required_parts
            elif operator == "==":
                return current_parts == required_parts
            else:
                return False
                
        except Exception:
            return False
    
    def _is_api_compatible(self, plugin_api_version: str) -> bool:
        """检查API版本兼容性"""
        try:
            # 简化的API兼容性检查：主版本号必须相同
            app_major = int(self._api_version.split('.')[0])
            plugin_major = int(plugin_api_version.split('.')[0])
            return app_major == plugin_major
        except Exception:
            return False
    
    def get_version_info(self) -> Dict[str, str]:
        """获取版本信息"""
        return {
            'app_version': self._app_version,
            'api_version': self._api_version
        }


class CodeAnalyzer:
    """代码安全分析器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        
        # 危险函数模式
        self._dangerous_patterns = {
            'eval': re.compile(r'\beval\s*\('),
            'exec': re.compile(r'\bexec\s*\('),
            'compile': re.compile(r'\bcompile\s*\('),
            'open': re.compile(r'\bopen\s*\('),
            '__import__': re.compile(r'\b__import__\s*\('),
            'subprocess': re.compile(r'\bsubprocess\.'),
            'os.system': re.compile(r'\bos\.system\s*\('),
            'os.popen': re.compile(r'\bos\.popen\s*\('),
            'input': re.compile(r'\binput\s*\('),
            'raw_input': re.compile(r'\braw_input\s*\('),
        }
        
        # 危险模块
        self._dangerous_modules = {
            'subprocess', 'os', 'sys', 'socket', 'urllib', 'requests',
            'ftplib', 'smtplib', 'telnetlib', 'pickle', 'marshal',
            'ctypes', 'winreg', 'nt', 'posix'
        }
    
    def analyze_code(self, code: str, policy: SecurityPolicy) -> List[SecurityViolation]:
        """分析代码安全性"""
        violations = []
        
        try:
            # AST语法分析
            tree = ast.parse(code)
            violations.extend(self._analyze_ast(tree, policy))
            
            # 模式匹配分析
            violations.extend(self._analyze_patterns(code, policy))
            
            # 导入分析
            violations.extend(self._analyze_imports(tree, policy))
            
        except SyntaxError as e:
            violations.append(SecurityViolation(
                plugin_id="unknown",
                violation_type="syntax_error",
                description=f"代码语法错误: {e}",
                severity="high"
            ))
        except Exception as e:
            self._logger.error(f"代码分析失败: {e}")
            violations.append(SecurityViolation(
                plugin_id="unknown",
                violation_type="analysis_error",
                description=f"代码分析失败: {e}",
                severity="medium"
            ))
        
        return violations
    
    def _analyze_ast(self, tree: ast.AST, policy: SecurityPolicy) -> List[SecurityViolation]:
        """AST分析"""
        violations = []
        
        class SecurityVisitor(ast.NodeVisitor):
            def __init__(self, violations_list, blocked_functions):
                self.violations = violations_list
                self.blocked_functions = blocked_functions
            
            def visit_Call(self, node):
                # 检查函数调用
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in self.blocked_functions:
                        self.violations.append(SecurityViolation(
                            plugin_id="unknown",
                            violation_type="blocked_function",
                            description=f"使用了被禁止的函数: {func_name}",
                            severity="high"
                        ))
                
                self.generic_visit(node)
        
        visitor = SecurityVisitor(violations, policy.blocked_functions)
        visitor.visit(tree)
        
        return violations
    
    def _analyze_patterns(self, code: str, policy: SecurityPolicy) -> List[SecurityViolation]:
        """模式匹配分析"""
        violations = []
        
        for pattern_name, pattern in self._dangerous_patterns.items():
            if pattern.search(code):
                violations.append(SecurityViolation(
                    plugin_id="unknown",
                    violation_type="dangerous_pattern",
                    description=f"检测到危险模式: {pattern_name}",
                    severity="high"
                ))
        
        return violations
    
    def _analyze_imports(self, tree: ast.AST, policy: SecurityPolicy) -> List[SecurityViolation]:
        """导入分析"""
        violations = []
        
        class ImportVisitor(ast.NodeVisitor):
            def __init__(self, violations_list, allowed_modules, dangerous_modules):
                self.violations = violations_list
                self.allowed_modules = allowed_modules
                self.dangerous_modules = dangerous_modules
            
            def visit_Import(self, node):
                for alias in node.names:
                    self._check_module(alias.name)
            
            def visit_ImportFrom(self, node):
                if node.module:
                    self._check_module(node.module)
            
            def _check_module(self, module_name):
                # 检查是否为危险模块
                if module_name in self.dangerous_modules:
                    self.violations.append(SecurityViolation(
                        plugin_id="unknown",
                        violation_type="dangerous_import",
                        description=f"导入危险模块: {module_name}",
                        severity="high"
                    ))
                
                # 检查是否在允许列表中
                if self.allowed_modules and not any(module_name.startswith(allowed) for allowed in self.allowed_modules):
                    self.violations.append(SecurityViolation(
                        plugin_id="unknown",
                        violation_type="unauthorized_import",
                        description=f"导入未授权模块: {module_name}",
                        severity="medium"
                    ))
        
        visitor = ImportVisitor(violations, policy.allowed_modules, self._dangerous_modules)
        visitor.visit(tree)
        
        return violations


class PluginSandbox:
    """插件沙箱"""
    
    def __init__(self, plugin_id: str, policy: SecurityPolicy, logger: Optional[logging.Logger] = None):
        self.plugin_id = plugin_id
        self.policy = policy
        self._logger = logger or logging.getLogger(__name__)
        self._code_analyzer = CodeAnalyzer(logger)
        self._execution_stats = {
            'start_time': 0,
            'memory_usage': 0,
            'violations': []
        }
    
    def validate_code(self, code: str) -> Tuple[bool, List[SecurityViolation]]:
        """验证代码安全性"""
        violations = self._code_analyzer.analyze_code(code, self.policy)
        
        # 过滤违规级别
        critical_violations = [v for v in violations if v.severity in ['high', 'critical']]
        
        is_safe = len(critical_violations) == 0
        return is_safe, violations
    
    def execute_in_sandbox(self, code: str, globals_dict: Optional[Dict] = None, 
                          locals_dict: Optional[Dict] = None) -> Tuple[bool, Any, List[SecurityViolation]]:
        """在沙箱中执行代码"""
        try:
            # 验证代码
            is_safe, violations = self.validate_code(code)
            if not is_safe:
                return False, None, violations
            
            # 准备受限的执行环境
            restricted_globals = self._create_restricted_globals(globals_dict)
            restricted_locals = locals_dict or {}
            
            # 设置执行限制
            self._execution_stats['start_time'] = time.time()
            
            # 执行代码
            result = None
            exec(code, restricted_globals, restricted_locals)
            
            # 检查执行时间
            execution_time = time.time() - self._execution_stats['start_time']
            if execution_time > self.policy.execution_timeout:
                violations.append(SecurityViolation(
                    plugin_id=self.plugin_id,
                    violation_type="timeout",
                    description=f"执行超时: {execution_time:.2f}s > {self.policy.execution_timeout}s",
                    severity="medium"
                ))
            
            return True, result, violations
            
        except Exception as e:
            violation = SecurityViolation(
                plugin_id=self.plugin_id,
                violation_type="execution_error",
                description=f"执行错误: {e}",
                severity="medium",
                stack_trace=str(e)
            )
            return False, None, [violation]
    
    def _create_restricted_globals(self, base_globals: Optional[Dict] = None) -> Dict:
        """创建受限的全局环境"""
        if base_globals:
            restricted = base_globals.copy()
        else:
            restricted = {}
        
        # 移除危险函数
        dangerous_builtins = [
            'eval', 'exec', 'compile', 'open', 'file', 'input', 'raw_input',
            '__import__', 'reload', 'vars', 'locals', 'globals', 'dir'
        ]
        
        safe_builtins = {}
        for name in dir(__builtins__):
            if name not in dangerous_builtins:
                safe_builtins[name] = getattr(__builtins__, name)
        
        restricted['__builtins__'] = safe_builtins
        
        # 添加安全的导入函数
        restricted['__import__'] = self._safe_import
        
        return restricted
    
    def _safe_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        """安全的导入函数"""
        # 检查模块是否被允许
        if not any(name.startswith(allowed) for allowed in self.policy.allowed_modules):
            raise ImportError(f"模块 {name} 不在允许列表中")
        
        return __import__(name, globals, locals, fromlist, level)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        return self._execution_stats.copy()


class PluginSecurityManager:
    """插件安全管理器"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._version_manager = VersionManager(logger)
        self._default_policies: Dict[str, SecurityPolicy] = {}
        self._plugin_policies: Dict[str, SecurityPolicy] = {}
        self._sandboxes: Dict[str, PluginSandbox] = {}
        self._violations: List[SecurityViolation] = []
        self._lock = threading.RLock()
        
        # 初始化默认策略
        self._initialize_default_policies()
    
    def _initialize_default_policies(self):
        """初始化默认安全策略"""
        # 受限制策略（默认）
        self._default_policies['restricted'] = SecurityPolicy(
            level=SecurityLevel.RESTRICTED,
            allowed_permissions={
                PermissionType.PLUGIN_COMMUNICATION,
                PermissionType.CONFIGURATION_ACCESS
            },
            allowed_modules={
                'json', 'time', 'datetime', 'math', 'random',
                'collections', 'itertools', 'functools', 'typing',
                'logging', 'enum', 'dataclasses',
                'src.core.interfaces', 'src.core.plugin_manager'
            },
            blocked_functions={
                'eval', 'exec', 'compile', 'open', '__import__',
                'input', 'raw_input'
            },
            execution_timeout=30.0,
            memory_limit=64 * 1024 * 1024
        )
        
        # 沙箱策略
        self._default_policies['sandboxed'] = SecurityPolicy(
            level=SecurityLevel.SANDBOXED,
            allowed_permissions={PermissionType.PLUGIN_COMMUNICATION},
            allowed_modules={'json', 'time', 'math'},
            blocked_functions={
                'eval', 'exec', 'compile', 'open', '__import__',
                'input', 'raw_input', 'vars', 'locals', 'globals'
            },
            execution_timeout=10.0,
            memory_limit=32 * 1024 * 1024
        )
        
        # 无限制策略（仅用于信任插件）
        self._default_policies['unrestricted'] = SecurityPolicy(
            level=SecurityLevel.UNRESTRICTED,
            allowed_permissions=set(PermissionType),
            execution_timeout=300.0,
            memory_limit=256 * 1024 * 1024
        )
    
    def set_app_version(self, version: str):
        """设置应用程序版本"""
        self._version_manager.set_app_version(version)
    
    def set_api_version(self, version: str):
        """设置API版本"""
        self._version_manager.set_api_version(version)
    
    def validate_plugin_metadata(self, metadata: PluginMetadata) -> Tuple[bool, str]:
        """验证插件元数据"""
        # 版本兼容性检查
        is_compatible, message = self._version_manager.check_compatibility(metadata)
        if not is_compatible:
            return False, message
        
        # 权限检查
        if not self._validate_permissions(metadata.permissions):
            return False, "插件请求了不被允许的权限"
        
        return True, "验证通过"
    
    def _validate_permissions(self, requested_permissions: List[str]) -> bool:
        """验证权限请求"""
        try:
            for perm in requested_permissions:
                if perm not in [p.value for p in PermissionType]:
                    return False
            return True
        except Exception:
            return False
    
    def create_sandbox(self, plugin_id: str, policy_name: str = 'restricted') -> PluginSandbox:
        """为插件创建沙箱"""
        with self._lock:
            # 获取安全策略
            policy = self._plugin_policies.get(plugin_id)
            if not policy:
                policy = self._default_policies.get(policy_name, self._default_policies['restricted'])
            
            # 创建沙箱
            sandbox = PluginSandbox(plugin_id, policy, self._logger)
            self._sandboxes[plugin_id] = sandbox
            
            if self._logger:
                self._logger.info(f"为插件 {plugin_id} 创建沙箱，策略: {policy.level.value}")
            
            return sandbox
    
    def get_sandbox(self, plugin_id: str) -> Optional[PluginSandbox]:
        """获取插件沙箱"""
        return self._sandboxes.get(plugin_id)
    
    def remove_sandbox(self, plugin_id: str):
        """移除插件沙箱"""
        with self._lock:
            if plugin_id in self._sandboxes:
                del self._sandboxes[plugin_id]
                if self._logger:
                    self._logger.info(f"移除插件 {plugin_id} 的沙箱")
    
    def set_plugin_policy(self, plugin_id: str, policy: SecurityPolicy):
        """设置插件安全策略"""
        with self._lock:
            self._plugin_policies[plugin_id] = policy
            
            # 如果沙箱已存在，更新策略
            if plugin_id in self._sandboxes:
                self._sandboxes[plugin_id].policy = policy
    
    def get_plugin_policy(self, plugin_id: str) -> Optional[SecurityPolicy]:
        """获取插件安全策略"""
        return self._plugin_policies.get(plugin_id)
    
    def record_violation(self, violation: SecurityViolation):
        """记录安全违规"""
        with self._lock:
            violation.plugin_id = violation.plugin_id  # 确保插件ID正确
            self._violations.append(violation)
            
            if self._logger:
                self._logger.warning(
                    f"安全违规 - 插件: {violation.plugin_id}, "
                    f"类型: {violation.violation_type}, "
                    f"严重性: {violation.severity}, "
                    f"描述: {violation.description}"
                )
            
            # 限制违规记录数量
            if len(self._violations) > 1000:
                self._violations = self._violations[-500:]
    
    def get_violations(self, plugin_id: Optional[str] = None, 
                      limit: int = 100) -> List[SecurityViolation]:
        """获取安全违规记录"""
        with self._lock:
            violations = self._violations
            
            if plugin_id:
                violations = [v for v in violations if v.plugin_id == plugin_id]
            
            # 按时间倒序
            violations.sort(key=lambda v: v.timestamp, reverse=True)
            
            return violations[:limit]
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """获取安全统计"""
        with self._lock:
            total_violations = len(self._violations)
            
            # 按严重性统计
            by_severity = defaultdict(int)
            by_type = defaultdict(int)
            by_plugin = defaultdict(int)
            
            for violation in self._violations:
                by_severity[violation.severity] += 1
                by_type[violation.violation_type] += 1
                by_plugin[violation.plugin_id] += 1
            
            return {
                'total_violations': total_violations,
                'active_sandboxes': len(self._sandboxes),
                'policies_count': len(self._plugin_policies),
                'by_severity': dict(by_severity),
                'by_type': dict(by_type),
                'by_plugin': dict(by_plugin),
                'version_info': self._version_manager.get_version_info()
            }
    
    def export_security_report(self) -> Dict[str, Any]:
        """导出安全报告"""
        return {
            'timestamp': time.time(),
            'statistics': self.get_security_statistics(),
            'violations': [v.to_dict() for v in self._violations[-100:]],  # 最近100条违规
            'policies': {pid: policy.to_dict() for pid, policy in self._plugin_policies.items()},
            'sandboxes': list(self._sandboxes.keys())
        }


# 便捷函数
def create_security_manager(logger: Optional[logging.Logger] = None) -> PluginSecurityManager:
    """创建插件安全管理器"""
    return PluginSecurityManager(logger)


def create_default_policy(level: SecurityLevel = SecurityLevel.RESTRICTED) -> SecurityPolicy:
    """创建默认安全策略"""
    if level == SecurityLevel.UNRESTRICTED:
        return SecurityPolicy(
            level=level,
            allowed_permissions=set(PermissionType),
            execution_timeout=300.0,
            memory_limit=256 * 1024 * 1024
        )
    elif level == SecurityLevel.SANDBOXED:
        return SecurityPolicy(
            level=level,
            allowed_permissions={PermissionType.PLUGIN_COMMUNICATION},
            allowed_modules={'json', 'time', 'math'},
            blocked_functions={
                'eval', 'exec', 'compile', 'open', '__import__',
                'input', 'raw_input', 'vars', 'locals', 'globals'
            },
            execution_timeout=10.0,
            memory_limit=32 * 1024 * 1024
        )
    else:  # RESTRICTED
        return SecurityPolicy(
            level=level,
            allowed_permissions={
                PermissionType.PLUGIN_COMMUNICATION,
                PermissionType.CONFIGURATION_ACCESS
            },
            allowed_modules={
                'json', 'time', 'datetime', 'math', 'random',
                'collections', 'itertools', 'functools', 'typing',
                'logging', 'enum', 'dataclasses',
                'src.core.interfaces', 'src.core.plugin_manager'
            },
            blocked_functions={
                'eval', 'exec', 'compile', 'open', '__import__',
                'input', 'raw_input'
            },
            execution_timeout=30.0,
            memory_limit=64 * 1024 * 1024
        )