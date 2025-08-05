#!/usr/bin/env python3
"""
混合数据管理器
HybridDataManager - 统一管理数据库和文件系统
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session

# 导入现有的数据管理组件
from .project_manager import ProjectDataManager
from .hole_manager import HoleDataManager
from .data_templates import DataTemplates, DataValidator

# 导入数据库模型
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# 避免导入Qt相关模块，直接导入需要的模型
try:
    from modules.models import DatabaseManager, Workpiece, Hole, Measurement
except ImportError:
    # 如果导入失败，创建模拟类用于测试
    class DatabaseManager:
        def __init__(self, url): pass
        def get_session(self): return None
        def close_session(self, session): pass

    class Workpiece:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class Hole:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class Measurement:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class HybridDataManager:
    """混合数据管理器 - 统一管理数据库和文件系统"""
    
    def __init__(self, data_root: str = "data", database_url: str = "sqlite:///Data/Databases/detection_system.db"):
        """
        初始化混合数据管理器
        
        Args:
            data_root: 文件系统数据根目录
            database_url: 数据库连接URL
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化文件系统管理器
        self.project_manager = ProjectDataManager(data_root)
        self.hole_manager = HoleDataManager(self.project_manager)
        self.validator = DataValidator()
        
        # 初始化数据库管理器
        self.db_manager = DatabaseManager(database_url)
        
        self.logger.info("混合数据管理器初始化完成")
    
    def create_project_from_dxf(self, dxf_file_path: str, project_name: str, 
                               holes_data: List[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """
        从DXF文件创建项目（数据库+文件系统）
        
        Args:
            dxf_file_path: DXF文件路径
            project_name: 项目名称
            holes_data: 孔位数据列表
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (项目ID, 项目路径)
        """
        try:
            # 1. 创建文件系统项目
            project_id, project_path = self.project_manager.create_project(
                dxf_file_path, project_name
            )
            
            # 2. 创建数据库记录
            session = self.db_manager.get_session()
            try:
                # 创建工件记录
                workpiece = Workpiece(
                    workpiece_id=project_id,
                    name=project_name,
                    type="DXF导入",
                    material="",
                    dxf_file_path=dxf_file_path,
                    project_data_path=project_path,
                    hole_count=len(holes_data),
                    status="active",
                    description=f"从DXF文件 {os.path.basename(dxf_file_path)} 创建的项目"
                )
                session.add(workpiece)
                session.flush()  # 获取workpiece.id
                
                # 3. 创建孔位记录（数据库+文件系统）
                for hole_data in holes_data:
                    # 验证孔位数据
                    hole_info = DataTemplates.create_hole_info_template(
                        hole_data["hole_id"], 
                        hole_data["position"],
                        hole_data.get("diameter", 8.865),
                        hole_data.get("depth", 900.0)
                    )
                    
                    is_valid, errors = self.validator.validate_hole_info(hole_info)
                    if not is_valid:
                        self.logger.warning(f"孔位数据验证失败 {hole_data['hole_id']}: {errors}")
                        continue
                    
                    # 创建文件系统孔位目录
                    success = self.hole_manager.create_hole_directory(
                        project_id, hole_data["hole_id"], hole_info
                    )
                    if not success:
                        self.logger.error(f"创建孔位目录失败: {hole_data['hole_id']}")
                        continue
                    
                    # 创建数据库孔位记录
                    hole_path = self.hole_manager.get_hole_path(project_id, hole_data["hole_id"])
                    
                    hole = Hole(
                        hole_id=hole_data["hole_id"],
                        workpiece_id=workpiece.id,
                        position_x=hole_data["position"]["x"],
                        position_y=hole_data["position"]["y"],
                        target_diameter=hole_data.get("diameter", 8.865),
                        tolerance=hole_data.get("tolerance", 0.1),
                        depth=hole_data.get("depth", 900.0),
                        file_system_path=hole_path,
                        status="pending"
                    )
                    session.add(hole)
                
                session.commit()
                self.logger.info(f"项目创建成功: {project_id}")
                return project_id, project_path
                
            except Exception as e:
                session.rollback()
                self.logger.error(f"数据库操作失败: {e}")
                # 清理文件系统
                if project_path and Path(project_path).exists():
                    import shutil
                    shutil.rmtree(project_path)
                return None, None
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            self.logger.error(f"创建项目失败: {e}")
            return None, None
    
    def sync_database_to_filesystem(self, project_id: str) -> bool:
        """
        将数据库数据同步到文件系统
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 同步是否成功
        """
        try:
            session = self.db_manager.get_session()
            try:
                # 获取工件信息
                workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                if not workpiece:
                    self.logger.error(f"项目不存在: {project_id}")
                    return False
                
                # 更新项目元数据
                updates = {
                    "total_holes": workpiece.hole_count,
                    "completed_holes": workpiece.completed_holes,
                    "status": workpiece.status,
                    "description": workpiece.description,
                    "version": workpiece.version
                }
                
                success = self.project_manager.update_project_metadata(project_id, updates)
                if not success:
                    return False
                
                # 同步孔位数据
                holes = session.query(Hole).filter_by(workpiece_id=workpiece.id).all()
                for hole in holes:
                    # 更新孔位信息
                    hole_info = {
                        "hole_id": hole.hole_id,
                        "position": {"x": hole.position_x, "y": hole.position_y},
                        "diameter": hole.target_diameter,
                        "depth": hole.depth,
                        "tolerance": hole.tolerance,
                        "status": hole.status,
                        "last_measurement_at": hole.last_measurement_at.isoformat() if hole.last_measurement_at else None,
                        "measurement_count": hole.measurement_count
                    }
                    
                    self.hole_manager.save_hole_info(project_id, hole.hole_id, hole_info)
                    
                    # 更新孔位状态
                    status_data = {
                        "current_status": hole.status,
                        "last_updated": hole.updated_at.isoformat() if hole.updated_at else datetime.now().isoformat(),
                        "measurement_count": hole.measurement_count
                    }
                    
                    self.hole_manager.save_hole_status(project_id, hole.hole_id, status_data)
                
                self.logger.info(f"数据库到文件系统同步成功: {project_id}")
                return True
                
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            self.logger.error(f"数据库到文件系统同步失败: {e}")
            return False
    
    def sync_filesystem_to_database(self, project_id: str) -> bool:
        """
        将文件系统数据同步到数据库
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 同步是否成功
        """
        try:
            # 获取文件系统项目元数据
            metadata = self.project_manager.get_project_metadata(project_id)
            if not metadata:
                self.logger.error(f"文件系统项目不存在: {project_id}")
                return False
            
            session = self.db_manager.get_session()
            try:
                # 更新或创建工件记录
                workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                if workpiece:
                    # 更新现有记录
                    workpiece.hole_count = metadata.get("total_holes", 0)
                    workpiece.completed_holes = metadata.get("completed_holes", 0)
                    workpiece.status = metadata.get("status", "active")
                    workpiece.description = metadata.get("description", "")
                    workpiece.version = metadata.get("version", "1.0")
                    workpiece.updated_at = datetime.now()
                else:
                    # 创建新记录
                    workpiece = Workpiece(
                        workpiece_id=project_id,
                        name=metadata.get("project_name", "未知项目"),
                        type="文件系统导入",
                        dxf_file_path=metadata.get("dxf_file_path", ""),
                        project_data_path=self.project_manager.get_project_path(project_id),
                        hole_count=metadata.get("total_holes", 0),
                        completed_holes=metadata.get("completed_holes", 0),
                        status=metadata.get("status", "active"),
                        description=metadata.get("description", "")
                    )
                    session.add(workpiece)
                    session.flush()
                
                # 同步孔位数据
                holes_dir = self.project_manager.get_holes_directory(project_id)
                if holes_dir:
                    holes_path = Path(holes_dir)
                    for hole_dir in holes_path.iterdir():
                        if hole_dir.is_dir():
                            hole_id = hole_dir.name
                            
                            # 获取孔位信息
                            hole_info = self.hole_manager.get_hole_info(project_id, hole_id)
                            hole_status = self.hole_manager.get_hole_status(project_id, hole_id)
                            
                            if hole_info and hole_status:
                                # 更新或创建孔位记录
                                hole = session.query(Hole).filter_by(
                                    workpiece_id=workpiece.id, hole_id=hole_id
                                ).first()
                                
                                if hole:
                                    # 更新现有记录
                                    hole.position_x = hole_info["position"]["x"]
                                    hole.position_y = hole_info["position"]["y"]
                                    hole.target_diameter = hole_info["diameter"]
                                    hole.depth = hole_info.get("depth", 900.0)
                                    hole.status = hole_status["current_status"]
                                    hole.measurement_count = hole_status.get("statistics", {}).get("total_measurements", 0)
                                    hole.updated_at = datetime.now()
                                else:
                                    # 创建新记录
                                    hole = Hole(
                                        hole_id=hole_id,
                                        workpiece_id=workpiece.id,
                                        position_x=hole_info["position"]["x"],
                                        position_y=hole_info["position"]["y"],
                                        target_diameter=hole_info["diameter"],
                                        tolerance=hole_info.get("tolerance", 0.1),
                                        depth=hole_info.get("depth", 900.0),
                                        file_system_path=str(hole_dir),
                                        status=hole_status["current_status"],
                                        measurement_count=hole_status.get("statistics", {}).get("total_measurements", 0)
                                    )
                                    session.add(hole)
                
                session.commit()
                self.logger.info(f"文件系统到数据库同步成功: {project_id}")
                return True
                
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            self.logger.error(f"文件系统到数据库同步失败: {e}")
            return False
    
    def get_hole_data_path(self, hole_id: str, project_id: Optional[str] = None) -> Optional[str]:
        """
        获取孔位数据路径（优先从数据库查询）
        
        Args:
            hole_id: 孔位ID
            project_id: 项目ID（可选）
            
        Returns:
            Optional[str]: 孔位数据路径
        """
        try:
            session = self.db_manager.get_session()
            try:
                # 从数据库查询
                query = session.query(Hole).filter_by(hole_id=hole_id)
                if project_id:
                    workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                    if workpiece:
                        query = query.filter_by(workpiece_id=workpiece.id)
                
                hole = query.first()
                if hole and hole.file_system_path:
                    return hole.file_system_path
                
                # 如果数据库中没有，尝试从文件系统查找
                if project_id:
                    return self.hole_manager.get_hole_path(project_id, hole_id)
                
                return None
                
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            self.logger.error(f"获取孔位数据路径失败: {e}")
            return None
    
    def ensure_data_consistency(self, project_id: str) -> bool:
        """
        确保数据一致性（双向同步）
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 一致性检查是否成功
        """
        try:
            # 先从文件系统同步到数据库
            fs_to_db_success = self.sync_filesystem_to_database(project_id)
            
            # 再从数据库同步到文件系统
            db_to_fs_success = self.sync_database_to_filesystem(project_id)
            
            success = fs_to_db_success and db_to_fs_success
            
            if success:
                self.logger.info(f"数据一致性确保成功: {project_id}")
            else:
                self.logger.warning(f"数据一致性确保部分失败: {project_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"数据一致性确保失败: {e}")
            return False
    
    def get_project_summary(self, project_id: str) -> Optional[Dict]:
        """
        获取项目摘要（合并数据库和文件系统信息）
        
        Args:
            project_id: 项目ID
            
        Returns:
            Optional[Dict]: 项目摘要信息
        """
        try:
            # 获取文件系统信息
            fs_metadata = self.project_manager.get_project_metadata(project_id)
            fs_stats = self.project_manager.get_project_statistics(project_id)
            
            # 获取数据库信息
            session = self.db_manager.get_session()
            try:
                workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                
                if not workpiece and not fs_metadata:
                    return None
                
                # 合并信息
                summary = {
                    "project_id": project_id,
                    "project_name": workpiece.name if workpiece else fs_metadata.get("project_name", ""),
                    "status": workpiece.status if workpiece else fs_metadata.get("status", "unknown"),
                    "created_at": workpiece.created_at.isoformat() if workpiece else fs_metadata.get("created_at", ""),
                    "updated_at": workpiece.updated_at.isoformat() if workpiece else "",
                    "dxf_file_path": workpiece.dxf_file_path if workpiece else fs_metadata.get("dxf_file", ""),
                    "project_data_path": workpiece.project_data_path if workpiece else self.project_manager.get_project_path(project_id),
                    "statistics": {
                        "total_holes": workpiece.hole_count if workpiece else fs_stats.get("total_holes", 0),
                        "completed_holes": workpiece.completed_holes if workpiece else fs_stats.get("completed_holes", 0),
                        "pending_holes": fs_stats.get("pending_holes", 0),
                        "error_holes": fs_stats.get("error_holes", 0),
                        "completion_rate": fs_stats.get("completion_rate", 0.0)
                    },
                    "data_sources": {
                        "database": workpiece is not None,
                        "filesystem": fs_metadata is not None
                    }
                }
                
                return summary
                
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            self.logger.error(f"获取项目摘要失败: {e}")
            return None
