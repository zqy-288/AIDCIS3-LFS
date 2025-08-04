"""
趋势分析器
"""

from typing import Dict, Any, List
from PySide6.QtCore import QObject, Signal
import numpy as np


class TrendAnalyzer(QObject):
    """趋势分析器"""
    
    analysis_completed = Signal(dict)
    
    def __init__(self, data_model=None):
        super().__init__()
        self.data_model = data_model
        
    def analyze_trend(self, data: List[float]) -> Dict[str, float]:
        """分析数据趋势"""
        if len(data) < 2:
            return {'slope': 0.0, 'trend': 'stable'}
            
        x = np.arange(len(data))
        slope = np.polyfit(x, data, 1)[0]
        
        if slope > 0.01:
            trend = 'increasing'
        elif slope < -0.01:
            trend = 'decreasing'
        else:
            trend = 'stable'
            
        return {'slope': float(slope), 'trend': trend}