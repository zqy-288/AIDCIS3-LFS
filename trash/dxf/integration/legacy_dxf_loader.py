#!/usr/bin/env python3
"""
向后兼容的DXF加载器
Legacy DXF Loader - 保持与现有UI的兼容性
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from core_business.dxf_parser import DXFParser
from core_business.models.hole_data import HoleCollection
from core_business.integration.ui_integration_adapter import UIIntegrationAdapter


class LegacyDXFLoader:
    """向后兼容的DXF加载器"""
    
    def __init__(self, data_root: str = "data", database_url: str = "sqlite:///detection_system.db"):
        """
        初始化向后兼容的DXF加载器
        
        Args:
            data_root: 数据根目录
            database_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        
        # 保持原有的DXF解析器用于兼容性
        self.dxf_parser = DXFParser()
        
        # 新的集成适配器
        self.ui_adapter = UIIntegrationAdapter(data_root, database_url)
        
        # 模式选择：legacy（仅解析）或 integrated（完整集成）
        self.mode = "integrated"  # 默认使用集成模式
        
        # 当前数据
        self.current_hole_collection: Optional[HoleCollection] = None
        self.current_file_path: Optional[str] = None
        
        self.logger.info("向后兼容DXF加载器初始化完成")
    
    def set_mode(self, mode: str):
        """
        设置加载模式
        
        Args:
            mode: "legacy" 或 "integrated"
        """
        if mode in ["legacy", "integrated"]:
            self.mode = mode
            self.logger.info(f"DXF加载模式设置为: {mode}")
        else:
            self.logger.warning(f"无效的模式: {mode}")
    
    def set_ui_callbacks(self, **callbacks):
        """设置UI回调函数"""
        self.ui_adapter.set_ui_callbacks(**callbacks)
    
    def load_dxf_file(self, file_path: str, project_name: Optional[str] = None) -> HoleCollection:
        """
        加载DXF文件（兼容原有接口）
        
        Args:
            file_path: DXF文件路径
            project_name: 项目名称（仅在集成模式下使用）
            
        Returns:
            HoleCollection: 孔位集合
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或解析失败
        """
        try:
            self.logger.info(f"加载DXF文件 ({self.mode}模式): {file_path}")
            
            # 基础验证
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise ValueError("DXF文件为空")
            
            self.current_file_path = file_path
            
            if self.mode == "legacy":
                # 传统模式：仅解析DXF，不创建项目
                return self._load_legacy_mode(file_path)
            else:
                # 集成模式：完整的项目创建和数据管理
                return self._load_integrated_mode(file_path, project_name)
                
        except (FileNotFoundError, ValueError) as e:
            # 重新抛出已知错误
            raise
        except Exception as e:
            error_msg = f"加载DXF文件失败: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _load_legacy_mode(self, file_path: str) -> HoleCollection:
        """传统模式加载"""
        self.logger.info("使用传统模式加载DXF")
        
        # 直接使用原有的DXF解析器
        hole_collection = self.dxf_parser.parse_file(file_path)
        
        if not hole_collection:
            raise ValueError("DXF文件解析失败，未返回有效数据")
        
        if len(hole_collection) == 0:
            self.logger.warning("DXF文件解析成功，但未找到符合条件的管孔")
        
        self.current_hole_collection = hole_collection
        self.logger.info(f"传统模式加载完成: {len(hole_collection)} 个孔位")
        
        return hole_collection
    
    def _load_integrated_mode(self, file_path: str, project_name: Optional[str]) -> HoleCollection:
        """集成模式加载"""
        self.logger.info("使用集成模式加载DXF")
        
        # 使用UI适配器加载
        result = self.ui_adapter.load_dxf_file(file_path, project_name)
        
        if not result["success"]:
            error_msg = result.get("error", "未知错误")
            raise ValueError(error_msg)
        
        hole_collection = result["hole_collection"]
        self.current_hole_collection = hole_collection
        
        self.logger.info(f"集成模式加载完成: {len(hole_collection)} 个孔位")
        
        return hole_collection
    
    def get_current_hole_collection(self) -> Optional[HoleCollection]:
        """获取当前孔位集合（兼容接口）"""
        return self.current_hole_collection
    
    def get_current_file_path(self) -> Optional[str]:
        """获取当前文件路径"""
        return self.current_file_path
    
    def get_project_info(self) -> Dict[str, Any]:
        """获取项目信息（仅在集成模式下有效）"""
        if self.mode == "integrated":
            return self.ui_adapter.get_project_info()
        else:
            return {
                "has_project": False,
                "mode": "legacy",
                "file_path": self.current_file_path,
                "hole_count": len(self.current_hole_collection) if self.current_hole_collection else 0
            }
    
    def navigate_to_realtime(self, hole_id: str) -> Dict[str, Any]:
        """导航到实时监控（仅在集成模式下有效）"""
        if self.mode == "integrated":
            return self.ui_adapter.navigate_to_realtime(hole_id)
        else:
            return {
                "success": False,
                "error": "传统模式不支持实时监控导航",
                "message": "请切换到集成模式"
            }
    
    def find_hole_by_position(self, x: float, y: float, tolerance: float = 1.0) -> Optional[str]:
        """根据位置查找孔位"""
        if self.mode == "integrated":
            return self.ui_adapter.find_hole_by_position(x, y, tolerance)
        else:
            # 传统模式下的简单查找
            if not self.current_hole_collection:
                return None
            
            for hole_id, hole_data in self.current_hole_collection.holes.items():
                dx = abs(hole_data.position.x - x)
                dy = abs(hole_data.position.y - y)
                
                if dx <= tolerance and dy <= tolerance:
                    return hole_id
            
            return None
    
    def get_hole_info(self, hole_id: str) -> Optional[Dict]:
        """获取孔位信息"""
        if self.mode == "integrated":
            return self.ui_adapter.get_hole_for_selection(hole_id)
        else:
            # 传统模式下的基础信息
            if not self.current_hole_collection or hole_id not in self.current_hole_collection.holes:
                return None
            
            hole_data = self.current_hole_collection.holes[hole_id]
            return {
                "hole_id": hole_id,
                "position": {"x": hole_data.position.x, "y": hole_data.position.y},
                "diameter": hole_data.diameter,
                "status": hole_data.status.value if hasattr(hole_data.status, 'value') else str(hole_data.status),
                "mode": "legacy"
            }
    
    def get_hole_list(self) -> list:
        """获取孔位列表"""
        if self.mode == "integrated":
            return self.ui_adapter.get_hole_list()
        else:
            # 传统模式下的基础列表
            if not self.current_hole_collection:
                return []
            
            hole_list = []
            for hole_id, hole_data in self.current_hole_collection.holes.items():
                hole_info = {
                    "hole_id": hole_id,
                    "position": {"x": hole_data.position.x, "y": hole_data.position.y},
                    "diameter": hole_data.diameter,
                    "status": hole_data.status.value if hasattr(hole_data.status, 'value') else str(hole_data.status),
                    "measurement_count": 0  # 传统模式下无测量数据
                }
                hole_list.append(hole_info)
            
            # 按孔位ID排序
            hole_list.sort(key=lambda x: x["hole_id"])
            return hole_list
    
    def update_hole_status(self, hole_id: str, status: str, reason: str = "") -> bool:
        """更新孔位状态"""
        if self.mode == "integrated":
            return self.ui_adapter.update_hole_status_ui(hole_id, status, reason)
        else:
            # 传统模式下仅更新内存中的状态
            if self.current_hole_collection and hole_id in self.current_hole_collection.holes:
                # 这里需要根据HoleData的实际结构来更新状态
                # 由于我们不能直接修改枚举值，这里只是记录日志
                self.logger.info(f"传统模式状态更新: {hole_id} -> {status} ({reason})")
                return True
            return False
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.mode == "integrated":
                self.ui_adapter.cleanup()
            
            self.current_hole_collection = None
            self.current_file_path = None
            
            self.logger.info("向后兼容DXF加载器清理完成")
        except Exception as e:
            self.logger.error(f"清理失败: {e}")
    
    def get_ui_adapter(self):
        """获取UI适配器（用于高级功能）"""
        return self.ui_adapter if self.mode == "integrated" else None
