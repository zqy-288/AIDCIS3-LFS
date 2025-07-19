#!/usr/bin/env python3
"""
孔位数据管理器
HoleDataManager - 管理孔位级别的数据操作
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging


class HoleDataManager:
    """孔位数据管理器类"""
    
    def __init__(self, project_manager):
        """
        初始化孔位数据管理器
        
        Args:
            project_manager: 项目数据管理器实例
        """
        self.project_manager = project_manager
        self.logger = logging.getLogger(__name__)
    
    def create_hole_directory(self, project_id: str, hole_id: str, hole_info: Dict) -> bool:
        """
        创建孔位目录结构
        
        Args:
            project_id: 项目ID
            hole_id: 孔位ID
            hole_info: 孔位基础信息
            
        Returns:
            bool: 创建是否成功
        """
        try:
            holes_dir = self.project_manager.get_holes_directory(project_id)
            if not holes_dir:
                self.logger.error(f"项目不存在: {project_id}")
                return False
            
            # 创建孔位目录
            hole_path = Path(holes_dir) / hole_id
            hole_path.mkdir(exist_ok=True)
            
            # 创建BISDM目录（基础信息和状态数据）
            bisdm_dir = hole_path / "BISDM"
            bisdm_dir.mkdir(exist_ok=True)
            
            # 创建CCIDM目录（测量数据CSV）
            ccidm_dir = hole_path / "CCIDM"
            ccidm_dir.mkdir(exist_ok=True)
            
            # 保存孔位基础信息
            self.save_hole_info(project_id, hole_id, hole_info)
            
            # 初始化状态信息
            initial_status = {
                "current_status": "pending",
                "status_history": [
                    {
                        "status": "pending",
                        "timestamp": datetime.now().isoformat(),
                        "reason": "初始化"
                    }
                ],
                "last_updated": datetime.now().isoformat()
            }
            self.save_hole_status(project_id, hole_id, initial_status)
            
            self.logger.info(f"孔位目录创建成功: {project_id}/{hole_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建孔位目录失败: {e}")
            return False
    
    def save_hole_info(self, project_id: str, hole_id: str, info_data: Dict) -> bool:
        """
        保存孔位基础信息
        
        Args:
            project_id: 项目ID
            hole_id: 孔位ID
            info_data: 孔位信息数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            hole_path = self.get_hole_path(project_id, hole_id)
            if not hole_path:
                return False
            
            # 添加时间戳
            info_data["created_at"] = info_data.get("created_at", datetime.now().isoformat())
            info_data["last_updated"] = datetime.now().isoformat()
            
            # 保存到BISDM/info.json
            info_file = Path(hole_path) / "BISDM" / "info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"孔位信息保存成功: {hole_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存孔位信息失败: {e}")
            return False
    
    def save_hole_status(self, project_id: str, hole_id: str, status_data: Dict) -> bool:
        """
        保存孔位状态信息
        
        Args:
            project_id: 项目ID
            hole_id: 孔位ID
            status_data: 状态数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            hole_path = self.get_hole_path(project_id, hole_id)
            if not hole_path:
                return False
            
            # 更新时间戳
            status_data["last_updated"] = datetime.now().isoformat()
            
            # 保存到BISDM/status.json
            status_file = Path(hole_path) / "BISDM" / "status.json"
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"孔位状态保存成功: {hole_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存孔位状态失败: {e}")
            return False
    
    def save_measurement_data(self, project_id: str, hole_id: str, measurement_data: List[Dict], 
                            filename: Optional[str] = None) -> bool:
        """
        保存测量数据到CSV文件
        
        Args:
            project_id: 项目ID
            hole_id: 孔位ID
            measurement_data: 测量数据列表
            filename: CSV文件名，如果不提供则自动生成
            
        Returns:
            bool: 保存是否成功
        """
        try:
            hole_path = self.get_hole_path(project_id, hole_id)
            if not hole_path:
                return False
            
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"measurement_{timestamp}.csv"
            
            # 保存到CCIDM目录
            csv_file = Path(hole_path) / "CCIDM" / filename

            # 使用csv模块保存数据
            if measurement_data:
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = measurement_data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(measurement_data)
            
            self.logger.info(f"测量数据保存成功: {hole_id}/{filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存测量数据失败: {e}")
            return False
    
    def get_hole_info(self, project_id: str, hole_id: str) -> Optional[Dict]:
        """
        获取孔位基础信息
        
        Args:
            project_id: 项目ID
            hole_id: 孔位ID
            
        Returns:
            Optional[Dict]: 孔位信息，如果不存在返回None
        """
        try:
            hole_path = self.get_hole_path(project_id, hole_id)
            if not hole_path:
                return None
            
            info_file = Path(hole_path) / "BISDM" / "info.json"
            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            self.logger.error(f"获取孔位信息失败: {e}")
            return None
    
    def get_hole_status(self, project_id: str, hole_id: str) -> Optional[Dict]:
        """
        获取孔位状态信息
        
        Args:
            project_id: 项目ID
            hole_id: 孔位ID
            
        Returns:
            Optional[Dict]: 状态信息，如果不存在返回None
        """
        try:
            hole_path = self.get_hole_path(project_id, hole_id)
            if not hole_path:
                return None
            
            status_file = Path(hole_path) / "BISDM" / "status.json"
            if status_file.exists():
                with open(status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            self.logger.error(f"获取孔位状态失败: {e}")
            return None
    
    def get_hole_measurements(self, project_id: str, hole_id: str) -> List[str]:
        """
        获取孔位的所有测量数据文件列表
        
        Args:
            project_id: 项目ID
            hole_id: 孔位ID
            
        Returns:
            List[str]: CSV文件路径列表
        """
        try:
            hole_path = self.get_hole_path(project_id, hole_id)
            if not hole_path:
                return []
            
            ccidm_dir = Path(hole_path) / "CCIDM"
            if ccidm_dir.exists():
                csv_files = list(ccidm_dir.glob("*.csv"))
                return [str(f) for f in sorted(csv_files)]
            return []
            
        except Exception as e:
            self.logger.error(f"获取测量数据文件失败: {e}")
            return []
    
    def load_measurement_data(self, csv_file_path: str) -> Optional[List[Dict]]:
        """
        加载测量数据CSV文件

        Args:
            csv_file_path: CSV文件路径

        Returns:
            Optional[List[Dict]]: 测量数据列表，如果失败返回None
        """
        try:
            if Path(csv_file_path).exists():
                with open(csv_file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            return None

        except Exception as e:
            self.logger.error(f"加载测量数据失败: {e}")
            return None
    
    def get_hole_path(self, project_id: str, hole_id: str) -> Optional[str]:
        """
        获取孔位目录路径
        
        Args:
            project_id: 项目ID
            hole_id: 孔位ID
            
        Returns:
            Optional[str]: 孔位目录路径
        """
        holes_dir = self.project_manager.get_holes_directory(project_id)
        if holes_dir:
            hole_path = Path(holes_dir) / hole_id
            if hole_path.exists():
                return str(hole_path)
        return None
    
    def update_hole_status(self, project_id: str, hole_id: str, new_status: str, reason: str = "") -> bool:
        """
        更新孔位状态
        
        Args:
            project_id: 项目ID
            hole_id: 孔位ID
            new_status: 新状态
            reason: 状态变更原因
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取当前状态
            current_status_data = self.get_hole_status(project_id, hole_id)
            if not current_status_data:
                return False
            
            # 添加状态历史记录
            status_history = current_status_data.get("status_history", [])
            status_history.append({
                "status": new_status,
                "timestamp": datetime.now().isoformat(),
                "reason": reason
            })
            
            # 更新状态数据
            updated_status = {
                "current_status": new_status,
                "status_history": status_history,
                "last_updated": datetime.now().isoformat()
            }
            
            return self.save_hole_status(project_id, hole_id, updated_status)
            
        except Exception as e:
            self.logger.error(f"更新孔位状态失败: {e}")
            return False
