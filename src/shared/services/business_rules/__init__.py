"""
业务规则服务模块
提供灵活的业务规则配置和动态调整能力
"""

from .rule_engine import (
    BusinessRuleEngine, 
    BusinessRule, 
    RuleType, 
    RulePriority, 
    RuleExecutionResult,
    apply_business_rules
)

__all__ = [
    'BusinessRuleEngine',
    'BusinessRule',
    'RuleType',
    'RulePriority',
    'RuleExecutionResult',
    'apply_business_rules'
]