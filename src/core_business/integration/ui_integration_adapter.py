#!/usr/bin/env python3
"""
UI集成适配器
UI Integration Adapter - 连接DXF集成管理器与UI组件
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path

from src.core_business.integration.dxf_integration_manager import DXFIntegrationManager
from src.core_business.models.hole_data import HoleCollection


class UIIntegrationAdapter:
    """UI集成适配器 - 为UI提供统一的数据管理接口"""
    
    def __init__(self, data_root: str = "data", database_url: str = "sqlite:///detection_system.db"):
        """
        初始化UI集成适配器
        
        Args:
            data_root: 数据根目录
            database_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化DXF集成管理器
        self.dxf_integration = DXFIntegrationManager(data_root, database_url)
        
        # UI回调函数
        self.ui_progress_callback: Optional[Callable] = None
        self.ui_status_callback: Optional[Callable] = None
        self.ui_error_callback: Optional[Callable] = None
        self.ui_completion_callback: Optional[Callable] = None
        
        # 设置集成管理器的回调
        self.dxf_integration.set_progress_callback(self._on_progress)
        self.dxf_integration.set_completion_callback(self._on_completion)
        self.dxf_integration.set_error_callback(self._on_error)
        
        self.logger.info("UI集成适配器初始化完成")
    
    def set_ui_callbacks(self, 
                        progress_callback: Optional[Callable] = None,
                        status_callback: Optional[Callable] = None,
                        error_callback: Optional[Callable] = None,
                        completion_callback: Optional[Callable] = None):
        """
        设置UI回调函数
        
        Args:
            progress_callback: 进度回调 (message: str, current: int, total: int)
            status_callback: 状态回调 (message: str)
            error_callback: 错误回调 (error_message: str)
            completion_callback: 完成回调 (project_id: str, summary: Dict)
        """
        self.ui_progress_callback = progress_callback
        self.ui_status_callback = status_callback
        self.ui_error_callback = error_callback
        self.ui_completion_callback = completion_callback
    
    def load_dxf_file(self, file_path: str, project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        加载DXF文件（UI友好的接口）
        
        Args:
            file_path: DXF文件路径
            project_name: 项目名称
            
        Returns:
            Dict[str, Any]: 加载结果
        """
        try:
            self.logger.info(f"UI适配器开始加载DXF: {file_path}")
            
            # 调用集成管理器加载
            success, project_id, hole_collection = self.dxf_integration.load_dxf_file_integrated(
                file_path, project_name
            )
            
            if success and project_id and hole_collection:
                # 获取项目摘要
                summary = self.dxf_integration.get_current_project_summary()
                
                result = {
                    "success": True,
                    "project_id": project_id,
                    "hole_collection": hole_collection,
                    "hole_count": len(hole_collection),
                    "file_name": Path(file_path).name,
                    "file_path": file_path,
                    "project_summary": summary,
                    "message": f"成功加载 {len(hole_collection)} 个孔位"
                }
                
                self.logger.info(f"DXF加载成功: {project_id}")
                return result
            else:
                return {
                    "success": False,
                    "error": "DXF文件加载失败",
                    "message": "请检查文件格式和内容"
                }
                
        except Exception as e:
            error_msg = f"DXF加载异常: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "message": "加载过程中发生错误"
            }
    
    def get_hole_for_selection(self, hole_id: str) -> Optional[Dict]:
        """
        获取孔位信息用于选择操作
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Optional[Dict]: 孔位信息
        """
        try:
            hole_data = self.dxf_integration.get_hole_for_realtime(hole_id)
            if hole_data:
                return {
                    "hole_id": hole_id,
                    "position": hole_data.get("basic_info", {}).get("position", {}),
                    "diameter": hole_data.get("basic_info", {}).get("diameter", 8.865),
                    "depth": hole_data.get("basic_info", {}).get("depth", 900.0),
                    "status": hole_data.get("status_info", {}).get("current_status", "pending"),
                    "measurement_count": hole_data.get("database_info", {}).get("measurement_count", 0),
                    "has_historical_data": hole_data.get("historical_data_available", False)
                }
            return None
            
        except Exception as e:
            self.logger.error(f"获取孔位信息失败: {e}")
            return None
    
    def navigate_to_realtime(self, hole_id: str) -> Dict[str, Any]:
        """
        导航到实时监控（UI友好的接口）
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Dict[str, Any]: 导航结果
        """
        try:
            success = self.dxf_integration.navigate_to_realtime_monitoring(hole_id)
            
            if success:
                hole_data = self.get_hole_for_selection(hole_id)
                return {
                    "success": True,
                    "hole_id": hole_id,
                    "hole_data": hole_data,
                    "message": f"成功导航到孔位 {hole_id} 的实时监控"
                }
            else:
                return {
                    "success": False,
                    "error": "导航失败",
                    "message": f"无法导航到孔位 {hole_id}"
                }
                
        except Exception as e:
            error_msg = f"导航异常: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "message": "导航过程中发生错误"
            }
    
    def get_project_info(self) -> Dict[str, Any]:
        """获取当前项目信息"""
        try:
            project_id = self.dxf_integration.get_current_project_id()
            if not project_id:
                return {"has_project": False}
            
            summary = self.dxf_integration.get_current_project_summary()
            statistics = self.dxf_integration.get_project_statistics()
            
            return {
                "has_project": True,
                "project_id": project_id,
                "project_name": summary.get("project_name", "") if summary else "",
                "dxf_file_path": summary.get("dxf_file_path", "") if summary else "",
                "statistics": statistics,
                "created_at": summary.get("created_at", "") if summary else "",
                "status": summary.get("status", "unknown") if summary else "unknown"
            }
            
        except Exception as e:
            self.logger.error(f"获取项目信息失败: {e}")
            return {"has_project": False, "error": str(e)}
    
    def find_hole_by_position(self, x: float, y: float, tolerance: float = 1.0) -> Optional[str]:
        """
        根据位置查找孔位
        
        Args:
            x: X坐标
            y: Y坐标
            tolerance: 容差
            
        Returns:
            Optional[str]: 孔位ID
        """
        return self.dxf_integration.get_hole_by_position(x, y, tolerance)
    
    def update_hole_status_ui(self, hole_id: str, status: str, reason: str = "") -> bool:
        """
        更新孔位状态（UI接口）
        
        Args:
            hole_id: 孔位ID
            status: 新状态
            reason: 原因
            
        Returns:
            bool: 更新是否成功
        """
        try:
            success = self.dxf_integration.update_hole_status(hole_id, status, reason)
            
            if success and self.ui_status_callback:
                self.ui_status_callback(f"孔位 {hole_id} 状态更新为: {status}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"更新孔位状态失败: {e}")
            return False
    
    def get_hole_list(self) -> List[Dict]:
        """获取孔位列表"""
        try:
            hole_collection = self.dxf_integration.get_current_hole_collection()
            if not hole_collection:
                return []
            
            hole_list = []
            for hole_id, hole_data in hole_collection.holes.items():
                # 获取扩展信息
                extended_data = self.get_hole_for_selection(hole_id)
                
                hole_info = {
                    "hole_id": hole_id,
                    "position": {"x": hole_data.position.x, "y": hole_data.position.y},
                    "diameter": hole_data.diameter,
                    "status": extended_data.get("status", "pending") if extended_data else "pending",
                    "measurement_count": extended_data.get("measurement_count", 0) if extended_data else 0
                }
                
                hole_list.append(hole_info)
            
            # 按孔位ID排序
            hole_list.sort(key=lambda x: x["hole_id"])
            return hole_list
            
        except Exception as e:
            self.logger.error(f"获取孔位列表失败: {e}")
            return []
    
    def cleanup(self):
        """清理资源"""
        try:
            self.dxf_integration.cleanup()
            self.logger.info("UI集成适配器清理完成")
        except Exception as e:
            self.logger.error(f"清理失败: {e}")
    
    def _on_progress(self, message: str, current: int, total: int):
        """进度回调处理"""
        if self.ui_progress_callback:
            self.ui_progress_callback(message, current, total)
    
    def _on_completion(self, project_id: str, summary: Dict):
        """完成回调处理"""
        if self.ui_completion_callback:
            self.ui_completion_callback(project_id, summary)
    
    def _on_error(self, error_message: str):
        """错误回调处理"""
        if self.ui_error_callback:
            self.ui_error_callback(error_message)
    
    def get_realtime_bridge(self):
        """获取实时数据桥梁（用于高级集成）"""
        return self.dxf_integration.realtime_bridge
    
    def get_hybrid_manager(self):
        """获取混合数据管理器（用于高级集成）"""
        return self.dxf_integration.hybrid_manager
