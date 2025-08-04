"""
质量指标计算器
"""

from typing import Dict, Any, List
from PySide6.QtCore import QObject, Signal


class QualityMetricsCalculator(QObject):
    """质量指标计算器"""
    
    calculation_completed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        
    def calculate_quality_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算质量指标"""
        if not data:
            return {'qualified_rate': 0.0, 'defect_rate': 0.0}
            
        total = len(data)
        qualified = sum(1 for item in data if item.get('status') == 'qualified')
        
        qualified_rate = (qualified / total) * 100 if total > 0 else 0.0
        defect_rate = 100.0 - qualified_rate
        
        return {
            'qualified_rate': qualified_rate,
            'defect_rate': defect_rate,
            'total_count': total,
            'qualified_count': qualified
        }