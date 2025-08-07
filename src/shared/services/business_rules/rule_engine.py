"""
业务规则配置系统
提供灵活的业务规则配置和动态调整能力
"""

import json
import yaml
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
import threading

from src.core.dependency_injection import injectable, ServiceLifetime
from src.core.error_handler import get_error_handler, error_handler, ErrorCategory
from src.core.data.config_manager import get_config
from src.shared.models.hole_data import HoleData, HoleCollection, HoleStatus


class RuleType(Enum):
    """业务规则类型"""
    VALIDATION = "validation"          # 验证规则
    CONVERSION = "conversion"          # 转换规则
    QUALITY_CHECK = "quality_check"    # 质量检查规则
    PERFORMANCE = "performance"        # 性能规则
    BUSINESS_LOGIC = "business_logic"  # 业务逻辑规则


class RulePriority(Enum):
    """规则优先级"""
    CRITICAL = "critical"    # 关键规则
    HIGH = "high"           # 高优先级
    MEDIUM = "medium"       # 中等优先级
    LOW = "low"             # 低优先级


@dataclass
class BusinessRule:
    """业务规则定义"""
    id: str                                    # 规则ID
    name: str                                  # 规则名称
    description: str                           # 规则描述
    rule_type: RuleType                        # 规则类型
    priority: RulePriority                     # 优先级
    enabled: bool = True                       # 是否启用
    parameters: Dict[str, Any] = field(default_factory=dict)  # 规则参数
    conditions: Dict[str, Any] = field(default_factory=dict)  # 触发条件
    actions: Dict[str, Any] = field(default_factory=dict)     # 执行动作
    created_at: Optional[datetime] = None      # 创建时间
    updated_at: Optional[datetime] = None      # 更新时间
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class RuleExecutionResult:
    """规则执行结果"""
    rule_id: str
    success: bool
    message: str
    execution_time: float
    data: Optional[Dict[str, Any]] = None


@injectable(ServiceLifetime.SINGLETON)
class BusinessRuleEngine:
    """业务规则引擎"""
    
    def __init__(self):
        self.error_handler = get_error_handler()
        self._lock = threading.RLock()
        
        # 规则存储
        self._rules: Dict[str, BusinessRule] = {}
        self._rule_chains: Dict[str, List[str]] = {}  # 规则链
        
        # 规则执行统计
        self._execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0.0
        }
        
        # 注册的规则处理器
        self._rule_handlers: Dict[str, Callable] = {}
        
        # 加载默认规则
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """加载默认业务规则"""
        default_rules = [
            # DXF解析规则
            BusinessRule(
                id="dxf_file_validation",
                name="DXF文件验证",
                description="验证DXF文件的有效性和完整性",
                rule_type=RuleType.VALIDATION,
                priority=RulePriority.CRITICAL,
                parameters={
                    "max_file_size_mb": get_config('aidcis2.dxf.max_file_size', 100),
                    "required_layers": get_config('aidcis2.dxf.required_layers', ["0"]),
                    "min_holes_count": get_config('aidcis2.dxf.min_holes', 1)
                }
            ),
            
            # 孔位质量检查规则
            BusinessRule(
                id="hole_quality_check",
                name="孔位质量检查",
                description="检查孔位数据的质量和准确性",
                rule_type=RuleType.QUALITY_CHECK,
                priority=RulePriority.HIGH,
                parameters={
                    "radius_tolerance": get_config('aidcis2.hole_radius_tolerance', 0.1),
                    "position_tolerance": get_config('aidcis2.position_tolerance', 0.01),
                    "expected_radius": get_config('aidcis2.expected_hole_radius', 8.865)
                }
            ),
            
            # 性能优化规则
            BusinessRule(
                id="performance_optimization",
                name="性能优化",
                description="应用性能优化策略",
                rule_type=RuleType.PERFORMANCE,
                priority=RulePriority.MEDIUM,
                parameters={
                    "cache_enabled": get_config('aidcis2.cache.enabled', True),
                    "parallel_processing": get_config('aidcis2.enable_parallel_processing', True),
                    "response_time_target_ms": get_config('aidcis2.response_time_target', 100)
                }
            ),
            
            # 数据转换规则
            BusinessRule(
                id="data_conversion_rules",
                name="数据转换规则",
                description="定义数据转换的标准和规范",
                rule_type=RuleType.CONVERSION,
                priority=RulePriority.HIGH,
                parameters={
                    "coordinate_precision": get_config('aidcis2.coordinate_precision', 3),
                    "angle_precision": get_config('aidcis2.angle_precision', 1),
                    "default_status": "pending"
                }
            ),
            
            # 业务逻辑规则
            BusinessRule(
                id="hole_identification_logic",
                name="孔位识别逻辑",
                description="定义孔位识别的业务逻辑",
                rule_type=RuleType.BUSINESS_LOGIC,
                priority=RulePriority.CRITICAL,
                parameters={
                    "min_arc_count": 2,
                    "max_boundary_radius": 100,
                    "angle_coverage_threshold": 350  # 度
                }
            )
        ]
        
        for rule in default_rules:
            self._rules[rule.id] = rule
    
    @error_handler(component="BusinessRuleEngine", category=ErrorCategory.BUSINESS)
    def add_rule(self, rule: BusinessRule) -> bool:
        """
        添加业务规则
        
        Args:
            rule: 业务规则对象
            
        Returns:
            是否添加成功
        """
        try:
            with self._lock:
                if rule.id in self._rules:
                    self.error_handler.handle_error(
                        ValueError(f"规则ID已存在: {rule.id}"),
                        component="BusinessRuleEngine"
                    )
                    return False
                
                self._rules[rule.id] = rule
                return True
                
        except Exception as e:
            self.error_handler.handle_error(e, component="BusinessRuleEngine")
            return False
    
    @error_handler(component="BusinessRuleEngine", category=ErrorCategory.BUSINESS)
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新业务规则
        
        Args:
            rule_id: 规则ID
            updates: 更新内容
            
        Returns:
            是否更新成功
        """
        try:
            with self._lock:
                if rule_id not in self._rules:
                    return False
                
                rule = self._rules[rule_id]
                
                # 更新规则属性
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                
                rule.updated_at = datetime.now()
                return True
                
        except Exception as e:
            self.error_handler.handle_error(e, component="BusinessRuleEngine")
            return False
    
    def get_rule(self, rule_id: str) -> Optional[BusinessRule]:
        """获取业务规则"""
        return self._rules.get(rule_id)
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[BusinessRule]:
        """按类型获取规则"""
        return [rule for rule in self._rules.values() if rule.rule_type == rule_type]
    
    def get_enabled_rules(self) -> List[BusinessRule]:
        """获取启用的规则"""
        return [rule for rule in self._rules.values() if rule.enabled]
    
    @error_handler(component="BusinessRuleEngine", category=ErrorCategory.BUSINESS)
    def execute_rule(self, rule_id: str, context: Dict[str, Any]) -> RuleExecutionResult:
        """
        执行业务规则
        
        Args:
            rule_id: 规则ID
            context: 执行上下文
            
        Returns:
            执行结果
        """
        start_time = datetime.now()
        
        try:
            rule = self._rules.get(rule_id)
            if not rule:
                return RuleExecutionResult(
                    rule_id=rule_id,
                    success=False,
                    message=f"规则不存在: {rule_id}",
                    execution_time=0.0
                )
            
            if not rule.enabled:
                return RuleExecutionResult(
                    rule_id=rule_id,
                    success=False,
                    message=f"规则已禁用: {rule_id}",
                    execution_time=0.0
                )
            
            # 检查触发条件
            if not self._check_conditions(rule, context):
                return RuleExecutionResult(
                    rule_id=rule_id,
                    success=True,
                    message="条件不满足，跳过执行",
                    execution_time=0.0
                )
            
            # 执行规则
            handler = self._rule_handlers.get(rule_id)
            if handler:
                result_data = handler(rule, context)
                success = True
                message = "规则执行成功"
            else:
                # 使用默认处理逻辑
                result_data = self._default_rule_handler(rule, context)
                success = True
                message = "使用默认处理器执行成功"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 更新统计
            self._update_execution_stats(execution_time, True)
            
            return RuleExecutionResult(
                rule_id=rule_id,
                success=success,
                message=message,
                execution_time=execution_time,
                data=result_data
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_execution_stats(execution_time, False)
            
            self.error_handler.handle_error(e, component="BusinessRuleEngine")
            
            return RuleExecutionResult(
                rule_id=rule_id,
                success=False,
                message=f"规则执行失败: {str(e)}",
                execution_time=execution_time
            )
    
    def _check_conditions(self, rule: BusinessRule, context: Dict[str, Any]) -> bool:
        """检查规则触发条件"""
        if not rule.conditions:
            return True
        
        for condition_key, condition_value in rule.conditions.items():
            context_value = context.get(condition_key)
            
            if isinstance(condition_value, dict):
                # 复杂条件检查
                if 'operator' in condition_value:
                    operator = condition_value['operator']
                    expected = condition_value['value']
                    
                    if operator == 'eq' and context_value != expected:
                        return False
                    elif operator == 'gt' and context_value <= expected:
                        return False
                    elif operator == 'lt' and context_value >= expected:
                        return False
                    elif operator == 'in' and context_value not in expected:
                        return False
            else:
                # 简单相等检查
                if context_value != condition_value:
                    return False
        
        return True
    
    def _default_rule_handler(self, rule: BusinessRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """默认规则处理器"""
        return {
            'rule_applied': True,
            'parameters_used': rule.parameters,
            'context_processed': True
        }
    
    def _update_execution_stats(self, execution_time: float, success: bool) -> None:
        """更新执行统计"""
        self._execution_stats['total_executions'] += 1
        
        if success:
            self._execution_stats['successful_executions'] += 1
        else:
            self._execution_stats['failed_executions'] += 1
        
        # 更新平均执行时间
        total = self._execution_stats['total_executions']
        current_avg = self._execution_stats['average_execution_time']
        self._execution_stats['average_execution_time'] = (
            (current_avg * (total - 1) + execution_time) / total
        )
    
    def register_rule_handler(self, rule_id: str, handler: Callable) -> None:
        """注册规则处理器"""
        self._rule_handlers[rule_id] = handler
    
    def execute_rule_chain(self, chain_name: str, context: Dict[str, Any]) -> List[RuleExecutionResult]:
        """执行规则链"""
        results = []
        
        if chain_name not in self._rule_chains:
            return results
        
        for rule_id in self._rule_chains[chain_name]:
            result = self.execute_rule(rule_id, context)
            results.append(result)
            
            # 如果关键规则失败，停止执行链
            rule = self._rules.get(rule_id)
            if rule and rule.priority == RulePriority.CRITICAL and not result.success:
                break
        
        return results
    
    def create_rule_chain(self, chain_name: str, rule_ids: List[str]) -> bool:
        """创建规则链"""
        # 验证所有规则ID都存在
        for rule_id in rule_ids:
            if rule_id not in self._rules:
                return False
        
        self._rule_chains[chain_name] = rule_ids
        return True
    
    def load_rules_from_file(self, file_path: str) -> bool:
        """从文件加载规则"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            if path.suffix.lower() == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif path.suffix.lower() in ['.yml', '.yaml']:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                return False
            
            # 解析规则
            for rule_data in data.get('rules', []):
                rule = BusinessRule(
                    id=rule_data['id'],
                    name=rule_data['name'],
                    description=rule_data.get('description', ''),
                    rule_type=RuleType(rule_data['type']),
                    priority=RulePriority(rule_data.get('priority', 'medium')),
                    enabled=rule_data.get('enabled', True),
                    parameters=rule_data.get('parameters', {}),
                    conditions=rule_data.get('conditions', {}),
                    actions=rule_data.get('actions', {})
                )
                self._rules[rule.id] = rule
            
            # 解析规则链
            for chain_data in data.get('rule_chains', []):
                self._rule_chains[chain_data['name']] = chain_data['rules']
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, component="BusinessRuleEngine")
            return False
    
    def save_rules_to_file(self, file_path: str) -> bool:
        """保存规则到文件"""
        try:
            data = {
                'rules': [
                    {
                        'id': rule.id,
                        'name': rule.name,
                        'description': rule.description,
                        'type': rule.rule_type.value,
                        'priority': rule.priority.value,
                        'enabled': rule.enabled,
                        'parameters': rule.parameters,
                        'conditions': rule.conditions,
                        'actions': rule.actions,
                        'created_at': rule.created_at.isoformat() if rule.created_at else None,
                        'updated_at': rule.updated_at.isoformat() if rule.updated_at else None
                    }
                    for rule in self._rules.values()
                ],
                'rule_chains': [
                    {'name': name, 'rules': rules}
                    for name, rules in self._rule_chains.items()
                ]
            }
            
            path = Path(file_path)
            if path.suffix.lower() == '.json':
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif path.suffix.lower() in ['.yml', '.yaml']:
                with open(path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            else:
                return False
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, component="BusinessRuleEngine")
            return False
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """获取规则统计信息"""
        return {
            'total_rules': len(self._rules),
            'enabled_rules': len(self.get_enabled_rules()),
            'rules_by_type': {
                rule_type.value: len(self.get_rules_by_type(rule_type))
                for rule_type in RuleType
            },
            'rules_by_priority': {
                priority.value: len([
                    rule for rule in self._rules.values() 
                    if rule.priority == priority
                ])
                for priority in RulePriority
            },
            'execution_stats': self._execution_stats.copy(),
            'rule_chains': len(self._rule_chains)
        }


# 便捷的规则应用装饰器
def apply_business_rules(rule_ids: Union[str, List[str]], 
                        context_builder: Optional[Callable] = None):
    """应用业务规则装饰器"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            from src.core.dependency_injection import get_container
            
            container = get_container()
            rule_engine = container.resolve(BusinessRuleEngine)
            
            # 构建执行上下文
            if context_builder:
                context = context_builder(*args, **kwargs)
            else:
                context = {'args': args, 'kwargs': kwargs}
            
            # 执行规则
            rule_list = rule_ids if isinstance(rule_ids, list) else [rule_ids]
            
            for rule_id in rule_list:
                result = rule_engine.execute_rule(rule_id, context)
                if not result.success:
                    raise RuntimeError(f"业务规则执行失败: {result.message}")
            
            # 执行原函数
            return func(*args, **kwargs)
        
        return wrapper
    return decorator