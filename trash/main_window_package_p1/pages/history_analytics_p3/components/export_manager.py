"""
导出管理器
"""

from typing import Dict, Any
from PySide6.QtCore import QObject, Signal
import json
import csv
from pathlib import Path


class ExportManager(QObject):
    """导出管理器"""
    
    export_completed = Signal(str)
    export_failed = Signal(str)
    
    def __init__(self):
        super().__init__()
        
    def export_to_json(self, data: Dict[str, Any], filepath: str):
        """导出为JSON格式"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.export_completed.emit(filepath)
        except Exception as e:
            self.export_failed.emit(str(e))
            
    def export_to_csv(self, data: list, filepath: str):
        """导出为CSV格式"""
        try:
            if not data:
                return
                
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            self.export_completed.emit(filepath)
        except Exception as e:
            self.export_failed.emit(str(e))