#!/usr/bin/env python3
"""
项目数据管理器
ProjectDataManager - 管理项目级别的数据操作
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging


class ProjectDataManager:
    """项目数据管理器类"""
    
    def __init__(self, data_root: str = "data"):
        """
        初始化项目数据管理器
        
        Args:
            data_root: 数据根目录路径
        """
        self.data_root = Path(data_root)
        self.logger = logging.getLogger(__name__)
        
        # 确保数据根目录存在
        self.data_root.mkdir(exist_ok=True)
        
    def create_project(self, dxf_file_path: str, project_name: str) -> Tuple[str, str]:
        """
        创建新项目
        
        Args:
            dxf_file_path: DXF文件路径
            project_name: 项目名称
            
        Returns:
            Tuple[str, str]: (项目ID, 项目路径)
        """
        try:
            # 生成项目ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dxf_name = Path(dxf_file_path).stem
            project_id = f"project_{dxf_name}_{timestamp}"
            
            # 创建项目目录
            project_path = self.data_root / project_id
            project_path.mkdir(exist_ok=True)
            
            # 创建子目录
            holes_dir = project_path / "holes"
            holes_dir.mkdir(exist_ok=True)
            
            # 复制DXF文件到项目目录
            dxf_dest = project_path / Path(dxf_file_path).name
            if Path(dxf_file_path).exists():
                shutil.copy2(dxf_file_path, dxf_dest)
            
            # 创建项目元数据
            metadata = {
                "project_id": project_id,
                "project_name": project_name,
                "dxf_file": Path(dxf_file_path).name,
                "dxf_file_path": str(dxf_dest),
                "created_at": datetime.now().isoformat(),
                "total_holes": 0,
                "completed_holes": 0,
                "status": "active",
                "version": "1.0"
            }
            
            # 保存元数据
            metadata_file = project_path / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"项目创建成功: {project_id}")
            return project_id, str(project_path)
            
        except Exception as e:
            self.logger.error(f"创建项目失败: {e}")
            raise
    
    def get_project_path(self, project_id: str) -> Optional[str]:
        """
        获取项目路径
        
        Args:
            project_id: 项目ID
            
        Returns:
            Optional[str]: 项目路径，如果不存在返回None
        """
        project_path = self.data_root / project_id
        if project_path.exists():
            return str(project_path)
        return None
    
    def get_project_metadata(self, project_id: str) -> Optional[Dict]:
        """
        获取项目元数据
        
        Args:
            project_id: 项目ID
            
        Returns:
            Optional[Dict]: 项目元数据，如果不存在返回None
        """
        try:
            project_path = self.data_root / project_id
            metadata_file = project_path / "metadata.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
            
        except Exception as e:
            self.logger.error(f"读取项目元数据失败: {e}")
            return None
    
    def update_project_metadata(self, project_id: str, updates: Dict) -> bool:
        """
        更新项目元数据
        
        Args:
            project_id: 项目ID
            updates: 要更新的字段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            metadata = self.get_project_metadata(project_id)
            if metadata is None:
                return False
            
            # 更新字段
            metadata.update(updates)
            metadata["last_updated"] = datetime.now().isoformat()
            
            # 保存更新后的元数据
            project_path = self.data_root / project_id
            metadata_file = project_path / "metadata.json"
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"项目元数据更新成功: {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新项目元数据失败: {e}")
            return False
    
    def list_projects(self) -> List[Dict]:
        """
        列出所有项目
        
        Returns:
            List[Dict]: 项目列表
        """
        projects = []
        
        try:
            for project_dir in self.data_root.iterdir():
                if project_dir.is_dir() and project_dir.name.startswith("project_"):
                    metadata = self.get_project_metadata(project_dir.name)
                    if metadata:
                        projects.append(metadata)
            
            # 按创建时间排序
            projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
        except Exception as e:
            self.logger.error(f"列出项目失败: {e}")
        
        return projects
    
    def delete_project(self, project_id: str) -> bool:
        """
        删除项目
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            project_path = self.data_root / project_id
            
            if project_path.exists():
                shutil.rmtree(project_path)
                self.logger.info(f"项目删除成功: {project_id}")
                return True
            else:
                self.logger.warning(f"项目不存在: {project_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"删除项目失败: {e}")
            return False
    
    def get_holes_directory(self, project_id: str) -> Optional[str]:
        """
        获取项目的孔位目录路径
        
        Args:
            project_id: 项目ID
            
        Returns:
            Optional[str]: 孔位目录路径
        """
        project_path = self.get_project_path(project_id)
        if project_path:
            holes_dir = Path(project_path) / "holes"
            if holes_dir.exists():
                return str(holes_dir)
        return None
    
    def get_project_statistics(self, project_id: str) -> Dict:
        """
        获取项目统计信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            Dict: 项目统计信息
        """
        stats = {
            "total_holes": 0,
            "completed_holes": 0,
            "pending_holes": 0,
            "error_holes": 0,
            "completion_rate": 0.0
        }
        
        try:
            holes_dir = self.get_holes_directory(project_id)
            if holes_dir:
                holes_path = Path(holes_dir)
                
                for hole_dir in holes_path.iterdir():
                    if hole_dir.is_dir():
                        stats["total_holes"] += 1
                        
                        # 检查孔位状态
                        status_file = hole_dir / "BISDM" / "status.json"
                        if status_file.exists():
                            with open(status_file, 'r', encoding='utf-8') as f:
                                status_data = json.load(f)
                                current_status = status_data.get("current_status", "pending")
                                
                                if current_status == "completed":
                                    stats["completed_holes"] += 1
                                elif current_status == "error":
                                    stats["error_holes"] += 1
                                else:
                                    stats["pending_holes"] += 1
                
                # 计算完成率
                if stats["total_holes"] > 0:
                    stats["completion_rate"] = stats["completed_holes"] / stats["total_holes"] * 100
            
        except Exception as e:
            self.logger.error(f"获取项目统计信息失败: {e}")
        
        return stats
