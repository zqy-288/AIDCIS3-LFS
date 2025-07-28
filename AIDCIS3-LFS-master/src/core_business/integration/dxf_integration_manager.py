#!/usr/bin/env python3
"""
DXF集成管理器
DXF Integration Manager - 集成DXF加载与数据管理系统
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime

# 导入现有组件
from src.core_business.dxf_parser import DXFParser
from src.core_business.models.hole_data import HoleData, HoleCollection
from src.core_business.data_management.hybrid_manager import HybridDataManager
from src.core_business.data_management.realtime_bridge import RealTimeDataBridge


class DXFIntegrationManager:
    """DXF集成管理器 - 统一管理DXF加载和数据集成"""
    
    def __init__(self, data_root: str = "data", database_url: str = "sqlite:///detection_system.db"):
        """
        初始化DXF集成管理器
        
        Args:
            data_root: 数据根目录
            database_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.dxf_parser = DXFParser()
        self.hybrid_manager = HybridDataManager(data_root, database_url)
        self.realtime_bridge = RealTimeDataBridge(self.hybrid_manager)
        
        # 回调函数
        self.progress_callback: Optional[Callable[[str, int, int], None]] = None
        self.completion_callback: Optional[Callable[[str, Dict], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None
        
        # 当前项目信息
        self.current_project_id: Optional[str] = None
        self.current_hole_collection: Optional[HoleCollection] = None
        
        self.logger.info("DXF集成管理器初始化完成")
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        """设置进度回调函数"""
        self.progress_callback = callback
    
    def set_completion_callback(self, callback: Callable[[str, Dict], None]):
        """设置完成回调函数"""
        self.completion_callback = callback
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """设置错误回调函数"""
        self.error_callback = callback
    
    def load_dxf_file_integrated(self, file_path: str, project_name: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[HoleCollection]]:
        """
        集成的DXF文件加载方法
        
        Args:
            file_path: DXF文件路径
            project_name: 项目名称（可选，默认使用文件名）
            
        Returns:
            Tuple[bool, Optional[str], Optional[HoleCollection]]: (成功标志, 项目ID, 孔位集合)
        """
        try:
            self.logger.info(f"开始集成DXF加载: {file_path}")
            
            # 1. 验证文件
            if not self._validate_file(file_path):
                return False, None, None
            
            # 2. 解析DXF文件
            self._report_progress("解析DXF文件", 1, 5)
            hole_collection = self.dxf_parser.parse_file(file_path)
            
            if not hole_collection or len(hole_collection) == 0:
                error_msg = "DXF文件解析成功，但未找到符合条件的孔位"
                self.logger.warning(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False, None, None
            
            self.logger.info(f"解析到 {len(hole_collection)} 个孔位")
            
            # 3. 准备项目数据
            self._report_progress("准备项目数据", 2, 5)
            if not project_name:
                project_name = Path(file_path).stem
            
            holes_data = self._convert_hole_collection_to_data(hole_collection)
            
            # 4. 创建项目
            self._report_progress("创建项目", 3, 5)
            project_id, project_path = self.hybrid_manager.create_project_from_dxf(
                file_path, project_name, holes_data
            )
            
            if not project_id:
                error_msg = "项目创建失败"
                self.logger.error(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False, None, None
            
            # 5. 数据同步
            self._report_progress("同步数据", 4, 5)
            sync_success = self.hybrid_manager.ensure_data_consistency(project_id)
            if not sync_success:
                self.logger.warning(f"数据同步部分失败: {project_id}")
            
            # 6. 完成
            self._report_progress("完成", 5, 5)
            
            # 保存当前项目信息
            self.current_project_id = project_id
            self.current_hole_collection = hole_collection
            
            # 获取项目摘要
            project_summary = self.hybrid_manager.get_project_summary(project_id)
            
            self.logger.info(f"DXF集成加载完成: {project_id}")
            
            # 调用完成回调
            if self.completion_callback:
                self.completion_callback(project_id, project_summary or {})
            
            return True, project_id, hole_collection
            
        except Exception as e:
            error_msg = f"DXF集成加载失败: {str(e)}"
            self.logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False, None, None
    
    def get_hole_for_realtime(self, hole_id: str) -> Optional[Dict]:
        """
        获取孔位数据用于实时监控
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Optional[Dict]: 孔位完整数据
        """
        if not self.current_project_id:
            self.logger.error("没有当前项目")
            return None
        
        return self.realtime_bridge.get_hole_complete_data(hole_id, self.current_project_id)
    
    def navigate_to_realtime_monitoring(self, hole_id: str) -> bool:
        """
        导航到实时监控
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            bool: 导航是否成功
        """
        if not self.current_project_id:
            self.logger.error("没有当前项目")
            return False
        
        return self.realtime_bridge.navigate_to_realtime(hole_id, self.current_project_id)
    
    def get_current_project_summary(self) -> Optional[Dict]:
        """获取当前项目摘要"""
        if not self.current_project_id:
            return None
        
        return self.hybrid_manager.get_project_summary(self.current_project_id)
    
    def get_current_hole_collection(self) -> Optional[HoleCollection]:
        """获取当前孔位集合"""
        return self.current_hole_collection
    
    def get_current_project_id(self) -> Optional[str]:
        """获取当前项目ID"""
        return self.current_project_id
    
    def _validate_file(self, file_path: str) -> bool:
        """验证文件"""
        try:
            if not os.path.exists(file_path):
                error_msg = f"文件不存在: {file_path}"
                self.logger.error(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                error_msg = "DXF文件为空"
                self.logger.error(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False
            
            # 检查文件扩展名
            if not file_path.lower().endswith('.dxf'):
                error_msg = "文件不是DXF格式"
                self.logger.error(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False
            
            return True
            
        except Exception as e:
            error_msg = f"文件验证失败: {str(e)}"
            self.logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
    
    def _convert_hole_collection_to_data(self, hole_collection: HoleCollection) -> List[Dict]:
        """将HoleCollection转换为数据管理系统需要的格式"""
        holes_data = []
        
        for hole_id, hole_data in hole_collection.holes.items():
            # 提取孔位信息
            hole_dict = {
                "hole_id": hole_id,
                "position": {
                    "x": hole_data.position.x,
                    "y": hole_data.position.y
                },
                "diameter": hole_data.diameter,
                "depth": getattr(hole_data, 'depth', 900.0),  # 默认深度
                "tolerance": getattr(hole_data, 'tolerance', 0.1)  # 默认公差
            }
            
            holes_data.append(hole_dict)
        
        return holes_data
    
    def _report_progress(self, message: str, current: int, total: int):
        """报告进度"""
        self.logger.info(f"进度 {current}/{total}: {message}")
        if self.progress_callback:
            self.progress_callback(message, current, total)
    
    def get_hole_by_position(self, x: float, y: float, tolerance: float = 1.0) -> Optional[str]:
        """
        根据位置查找孔位ID
        
        Args:
            x: X坐标
            y: Y坐标
            tolerance: 位置容差
            
        Returns:
            Optional[str]: 孔位ID
        """
        if not self.current_hole_collection:
            return None
        
        for hole_id, hole_data in self.current_hole_collection.holes.items():
            dx = abs(hole_data.position.x - x)
            dy = abs(hole_data.position.y - y)
            
            if dx <= tolerance and dy <= tolerance:
                return hole_id
        
        return None
    
    def get_project_statistics(self) -> Dict:
        """获取项目统计信息"""
        if not self.current_project_id:
            return {
                "total_holes": 0,
                "completed_holes": 0,
                "pending_holes": 0,
                "error_holes": 0,
                "completion_rate": 0.0
            }
        
        # 从混合管理器获取统计
        summary = self.hybrid_manager.get_project_summary(self.current_project_id)
        if summary:
            return summary.get("statistics", {})
        
        # 从项目管理器获取统计
        return self.hybrid_manager.project_manager.get_project_statistics(self.current_project_id)
    
    def update_hole_status(self, hole_id: str, status: str, reason: str = "") -> bool:
        """
        更新孔位状态
        
        Args:
            hole_id: 孔位ID
            status: 新状态
            reason: 状态变更原因
            
        Returns:
            bool: 更新是否成功
        """
        if not self.current_project_id:
            return False
        
        return self.realtime_bridge.update_hole_status(
            hole_id, self.current_project_id, status, reason
        )
    
    def save_measurement_data(self, hole_id: str, measurement_data: List[Dict]) -> bool:
        """
        保存测量数据
        
        Args:
            hole_id: 孔位ID
            measurement_data: 测量数据
            
        Returns:
            bool: 保存是否成功
        """
        if not self.current_project_id:
            return False
        
        return self.realtime_bridge.save_measurement_result(
            hole_id, self.current_project_id, measurement_data
        )
    
    def load_historical_data(self, hole_id: str) -> List[Dict]:
        """
        加载历史测量数据
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            List[Dict]: 历史测量数据
        """
        if not self.current_project_id:
            return []
        
        return self.realtime_bridge.load_historical_data(hole_id, self.current_project_id)
    
    def cleanup(self):
        """清理资源"""
        self.current_project_id = None
        self.current_hole_collection = None
        self.logger.info("DXF集成管理器资源清理完成")
