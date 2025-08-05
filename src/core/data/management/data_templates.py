#!/usr/bin/env python3
"""
数据模板和验证
Data Templates and Validation
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging


class DataTemplates:
    """数据模板类"""
    
    @staticmethod
    def create_project_metadata_template(project_id: str, project_name: str, 
                                       dxf_file: str, total_holes: int = 0) -> Dict:
        """
        创建项目元数据模板
        
        Args:
            project_id: 项目ID
            project_name: 项目名称
            dxf_file: DXF文件名
            total_holes: 总孔位数
            
        Returns:
            Dict: 项目元数据模板
        """
        return {
            "project_id": project_id,
            "project_name": project_name,
            "dxf_file": dxf_file,
            "created_at": datetime.now().isoformat(),
            "total_holes": total_holes,
            "completed_holes": 0,
            "status": "active",
            "version": "1.0",
            "description": "",
            "tags": [],
            "settings": {
                "auto_backup": True,
                "compression": False,
                "retention_days": 365
            }
        }
    
    @staticmethod
    def create_hole_info_template(hole_id: str, position: Dict[str, float], 
                                diameter: float = 8.865, depth: float = 900.0) -> Dict:
        """
        创建孔位信息模板
        
        Args:
            hole_id: 孔位ID
            position: 位置坐标 {"x": float, "y": float}
            diameter: 孔径
            depth: 深度
            
        Returns:
            Dict: 孔位信息模板
        """
        return {
            "hole_id": hole_id,
            "position": position,
            "diameter": diameter,
            "depth": depth,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "properties": {
                "material": "",
                "surface_finish": "",
                "tolerance": 0.1,
                "critical": False
            },
            "geometry": {
                "type": "circular",
                "nominal_diameter": diameter,
                "depth_range": {"min": 0.0, "max": depth}
            }
        }
    
    @staticmethod
    def create_hole_status_template(initial_status: str = "pending", reason: str = "初始化") -> Dict:
        """
        创建孔位状态模板
        
        Args:
            initial_status: 初始状态
            reason: 状态原因
            
        Returns:
            Dict: 孔位状态模板
        """
        timestamp = datetime.now().isoformat()
        
        return {
            "current_status": initial_status,
            "status_history": [
                {
                    "status": initial_status,
                    "timestamp": timestamp,
                    "reason": reason,
                    "operator": "system"
                }
            ],
            "last_updated": timestamp,
            "statistics": {
                "total_measurements": 0,
                "successful_measurements": 0,
                "failed_measurements": 0,
                "average_measurement_time": 0.0
            }
        }
    
    @staticmethod
    def create_measurement_data_template() -> List[Dict]:
        """
        创建测量数据模板
        
        Returns:
            List[Dict]: 测量数据模板
        """
        return [
            {
                "timestamp": datetime.now().isoformat(),
                "depth": 0.0,
                "diameter": 8.865,
                "temperature": 25.0,
                "pressure": 1013.25,
                "measurement_id": "M001",
                "quality": "good",
                "operator": "system"
            }
        ]


class DataValidator:
    """数据验证器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_project_metadata(self, metadata: Dict) -> tuple[bool, List[str]]:
        """
        验证项目元数据
        
        Args:
            metadata: 项目元数据
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        # 必需字段检查
        required_fields = ["project_id", "project_name", "dxf_file", "created_at", "status"]
        for field in required_fields:
            if field not in metadata:
                errors.append(f"缺少必需字段: {field}")
        
        # 数据类型检查
        if "total_holes" in metadata and not isinstance(metadata["total_holes"], int):
            errors.append("total_holes必须是整数")
        
        if "completed_holes" in metadata and not isinstance(metadata["completed_holes"], int):
            errors.append("completed_holes必须是整数")
        
        # 状态值检查
        valid_statuses = ["active", "completed", "paused", "error", "archived"]
        if "status" in metadata and metadata["status"] not in valid_statuses:
            errors.append(f"无效的状态值: {metadata['status']}")
        
        return len(errors) == 0, errors
    
    def validate_hole_info(self, hole_info: Dict) -> tuple[bool, List[str]]:
        """
        验证孔位信息
        
        Args:
            hole_info: 孔位信息
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        # 必需字段检查
        required_fields = ["hole_id", "position", "diameter", "depth"]
        for field in required_fields:
            if field not in hole_info:
                errors.append(f"缺少必需字段: {field}")
        
        # 位置信息检查
        if "position" in hole_info:
            position = hole_info["position"]
            if not isinstance(position, dict):
                errors.append("position必须是字典类型")
            else:
                if "x" not in position or "y" not in position:
                    errors.append("position必须包含x和y坐标")
                if not isinstance(position.get("x"), (int, float)):
                    errors.append("position.x必须是数字")
                if not isinstance(position.get("y"), (int, float)):
                    errors.append("position.y必须是数字")
        
        # 数值范围检查
        if "diameter" in hole_info:
            diameter = hole_info["diameter"]
            if not isinstance(diameter, (int, float)) or diameter <= 0:
                errors.append("diameter必须是正数")
        
        if "depth" in hole_info:
            depth = hole_info["depth"]
            if not isinstance(depth, (int, float)) or depth <= 0:
                errors.append("depth必须是正数")
        
        return len(errors) == 0, errors
    
    def validate_hole_status(self, status_data: Dict) -> tuple[bool, List[str]]:
        """
        验证孔位状态数据
        
        Args:
            status_data: 状态数据
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        # 必需字段检查
        required_fields = ["current_status", "status_history", "last_updated"]
        for field in required_fields:
            if field not in status_data:
                errors.append(f"缺少必需字段: {field}")
        
        # 状态值检查
        valid_statuses = ["pending", "in_progress", "completed", "error", "skipped"]
        if "current_status" in status_data:
            if status_data["current_status"] not in valid_statuses:
                errors.append(f"无效的状态值: {status_data['current_status']}")
        
        # 状态历史检查
        if "status_history" in status_data:
            history = status_data["status_history"]
            if not isinstance(history, list):
                errors.append("status_history必须是列表类型")
            else:
                for i, entry in enumerate(history):
                    if not isinstance(entry, dict):
                        errors.append(f"status_history[{i}]必须是字典类型")
                        continue
                    
                    required_entry_fields = ["status", "timestamp"]
                    for field in required_entry_fields:
                        if field not in entry:
                            errors.append(f"status_history[{i}]缺少字段: {field}")
        
        return len(errors) == 0, errors
    
    def validate_measurement_data(self, measurement_data: List[Dict]) -> tuple[bool, List[str]]:
        """
        验证测量数据
        
        Args:
            measurement_data: 测量数据列表
            
        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        if not isinstance(measurement_data, list):
            errors.append("measurement_data必须是列表类型")
            return False, errors
        
        # 检查每条测量记录
        for i, record in enumerate(measurement_data):
            if not isinstance(record, dict):
                errors.append(f"measurement_data[{i}]必须是字典类型")
                continue
            
            # 必需字段检查
            required_fields = ["timestamp", "depth", "diameter"]
            for field in required_fields:
                if field not in record:
                    errors.append(f"measurement_data[{i}]缺少字段: {field}")
            
            # 数值检查
            if "depth" in record and not isinstance(record["depth"], (int, float)):
                errors.append(f"measurement_data[{i}].depth必须是数字")
            
            if "diameter" in record and not isinstance(record["diameter"], (int, float)):
                errors.append(f"measurement_data[{i}].diameter必须是数字")
        
        return len(errors) == 0, errors


class DataExporter:
    """数据导出器类"""
    
    @staticmethod
    def export_project_summary(project_metadata: Dict, hole_statistics: Dict) -> Dict:
        """
        导出项目摘要
        
        Args:
            project_metadata: 项目元数据
            hole_statistics: 孔位统计信息
            
        Returns:
            Dict: 项目摘要
        """
        return {
            "project_info": {
                "id": project_metadata.get("project_id"),
                "name": project_metadata.get("project_name"),
                "created_at": project_metadata.get("created_at"),
                "status": project_metadata.get("status")
            },
            "statistics": hole_statistics,
            "export_timestamp": datetime.now().isoformat(),
            "export_version": "1.0"
        }
    
    @staticmethod
    def export_hole_report(hole_info: Dict, hole_status: Dict, measurements: List[str]) -> Dict:
        """
        导出孔位报告
        
        Args:
            hole_info: 孔位信息
            hole_status: 孔位状态
            measurements: 测量文件列表
            
        Returns:
            Dict: 孔位报告
        """
        return {
            "hole_info": hole_info,
            "current_status": hole_status.get("current_status"),
            "status_history": hole_status.get("status_history", []),
            "measurement_files": measurements,
            "total_measurements": len(measurements),
            "export_timestamp": datetime.now().isoformat()
        }
