#!/usr/bin/env python3
"""
实时数据桥梁
RealTimeDataBridge - 连接DXF预览和实时监控
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from sqlalchemy.orm import Session

# 导入数据管理组件
from .hybrid_manager import HybridDataManager

# 导入数据库模型
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.modules.models import DatabaseManager, Workpiece, Hole, Measurement


class RealTimeDataBridge:
    """实时数据桥梁类 - 连接DXF预览和实时监控"""
    
    def __init__(self, hybrid_manager: HybridDataManager):
        """
        初始化实时数据桥梁
        
        Args:
            hybrid_manager: 混合数据管理器实例
        """
        self.hybrid_manager = hybrid_manager
        self.db_manager = hybrid_manager.db_manager
        self.logger = logging.getLogger(__name__)
        
        # 回调函数
        self.navigation_callback: Optional[Callable] = None
        self.data_update_callback: Optional[Callable] = None
        self.status_update_callback: Optional[Callable] = None
        
        self.logger.info("实时数据桥梁初始化完成")
    
    def set_navigation_callback(self, callback: Callable[[str, Dict], None]):
        """
        设置导航回调函数
        
        Args:
            callback: 导航回调函数，参数为(hole_id, hole_data)
        """
        self.navigation_callback = callback
    
    def set_data_update_callback(self, callback: Callable[[str, List[Dict]], None]):
        """
        设置数据更新回调函数
        
        Args:
            callback: 数据更新回调函数，参数为(hole_id, measurement_data)
        """
        self.data_update_callback = callback
    
    def set_status_update_callback(self, callback: Callable[[str, str], None]):
        """
        设置状态更新回调函数
        
        Args:
            callback: 状态更新回调函数，参数为(hole_id, status)
        """
        self.status_update_callback = callback
    
    def navigate_to_realtime(self, hole_id: str, project_id: str) -> bool:
        """
        导航到实时监控界面
        
        Args:
            hole_id: 孔位ID
            project_id: 项目ID
            
        Returns:
            bool: 导航是否成功
        """
        try:
            # 获取孔位数据
            hole_data = self.get_hole_complete_data(hole_id, project_id)
            if not hole_data:
                self.logger.error(f"获取孔位数据失败: {hole_id}")
                return False
            
            # 更新孔位状态为"准备测量"
            success = self.update_hole_status(hole_id, project_id, "ready_for_measurement", "准备开始实时测量")
            if not success:
                self.logger.warning(f"更新孔位状态失败: {hole_id}")
            
            # 调用导航回调
            if self.navigation_callback:
                self.navigation_callback(hole_id, hole_data)
                self.logger.info(f"导航到实时监控成功: {hole_id}")
                return True
            else:
                self.logger.warning("导航回调函数未设置")
                return False
                
        except Exception as e:
            self.logger.error(f"导航到实时监控失败: {e}")
            return False
    
    def load_historical_data(self, hole_id: str, project_id: str) -> List[Dict]:
        """
        加载历史测量数据
        
        Args:
            hole_id: 孔位ID
            project_id: 项目ID
            
        Returns:
            List[Dict]: 历史测量数据列表
        """
        try:
            historical_data = []
            
            # 1. 从数据库加载
            db_data = self.load_database_measurements(hole_id, project_id)
            if db_data:
                historical_data.extend(db_data)
            
            # 2. 从文件系统加载
            fs_data = self.load_filesystem_measurements(hole_id, project_id)
            if fs_data:
                historical_data.extend(fs_data)
            
            # 3. 去重和排序
            historical_data = self.deduplicate_measurements(historical_data)
            historical_data.sort(key=lambda x: x.get("timestamp", ""))
            
            self.logger.info(f"加载历史数据成功: {hole_id}, {len(historical_data)}条记录")
            return historical_data
            
        except Exception as e:
            self.logger.error(f"加载历史数据失败: {e}")
            return []
    
    def start_realtime_measurement(self, hole_id: str, project_id: str, 
                                 measurement_params: Dict) -> bool:
        """
        开始实时测量
        
        Args:
            hole_id: 孔位ID
            project_id: 项目ID
            measurement_params: 测量参数
            
        Returns:
            bool: 启动是否成功
        """
        try:
            # 更新孔位状态
            success = self.update_hole_status(hole_id, project_id, "measuring", "开始实时测量")
            if not success:
                return False
            
            # 记录测量开始时间
            session = self.db_manager.get_session()
            try:
                workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                if workpiece:
                    hole = session.query(Hole).filter_by(
                        workpiece_id=workpiece.id, hole_id=hole_id
                    ).first()
                    if hole:
                        hole.last_measurement_at = datetime.now()
                        session.commit()
            finally:
                self.db_manager.close_session(session)
            
            # 调用状态更新回调
            if self.status_update_callback:
                self.status_update_callback(hole_id, "measuring")
            
            self.logger.info(f"开始实时测量: {hole_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"开始实时测量失败: {e}")
            return False
    
    def save_measurement_result(self, hole_id: str, project_id: str, 
                              measurement_data: List[Dict]) -> bool:
        """
        保存测量结果
        
        Args:
            hole_id: 孔位ID
            project_id: 项目ID
            measurement_data: 测量数据
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 1. 保存到文件系统
            fs_success = self.hybrid_manager.hole_manager.save_measurement_data(
                project_id, hole_id, measurement_data
            )
            
            # 2. 保存到数据库
            db_success = self.save_measurements_to_database(hole_id, project_id, measurement_data)
            
            # 3. 更新孔位状态和统计
            if fs_success and db_success:
                self.update_hole_status(hole_id, project_id, "completed", "测量完成")
                self.update_measurement_statistics(hole_id, project_id, len(measurement_data))
                
                # 调用数据更新回调
                if self.data_update_callback:
                    self.data_update_callback(hole_id, measurement_data)
                
                self.logger.info(f"保存测量结果成功: {hole_id}, {len(measurement_data)}条记录")
                return True
            else:
                self.logger.error(f"保存测量结果失败: {hole_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"保存测量结果失败: {e}")
            return False
    
    def get_hole_complete_data(self, hole_id: str, project_id: str) -> Optional[Dict]:
        """
        获取孔位完整数据
        
        Args:
            hole_id: 孔位ID
            project_id: 项目ID
            
        Returns:
            Optional[Dict]: 孔位完整数据
        """
        try:
            # 从文件系统获取基础信息
            hole_info = self.hybrid_manager.hole_manager.get_hole_info(project_id, hole_id)
            hole_status = self.hybrid_manager.hole_manager.get_hole_status(project_id, hole_id)
            
            # 从数据库获取扩展信息
            session = self.db_manager.get_session()
            try:
                workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                if workpiece:
                    hole = session.query(Hole).filter_by(
                        workpiece_id=workpiece.id, hole_id=hole_id
                    ).first()
                    
                    if hole_info and hole_status:
                        # 合并数据
                        complete_data = {
                            "hole_id": hole_id,
                            "project_id": project_id,
                            "basic_info": hole_info,
                            "status_info": hole_status,
                            "database_info": {
                                "target_diameter": hole.target_diameter if hole else hole_info.get("diameter"),
                                "tolerance": hole.tolerance if hole else hole_info.get("tolerance", 0.1),
                                "depth": hole.depth if hole else hole_info.get("depth"),
                                "measurement_count": hole.measurement_count if hole else 0,
                                "last_measurement_at": hole.last_measurement_at.isoformat() if hole and hole.last_measurement_at else None
                            },
                            "file_system_path": self.hybrid_manager.get_hole_data_path(hole_id, project_id),
                            "historical_data_available": len(self.load_historical_data(hole_id, project_id)) > 0
                        }
                        
                        return complete_data
                
                return None
                
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            self.logger.error(f"获取孔位完整数据失败: {e}")
            return None
    
    def load_database_measurements(self, hole_id: str, project_id: str) -> List[Dict]:
        """从数据库加载测量数据"""
        try:
            session = self.db_manager.get_session()
            try:
                workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                if not workpiece:
                    return []
                
                hole = session.query(Hole).filter_by(
                    workpiece_id=workpiece.id, hole_id=hole_id
                ).first()
                if not hole:
                    return []
                
                measurements = session.query(Measurement).filter_by(hole_id=hole.id).order_by(Measurement.depth).all()
                
                result = []
                for m in measurements:
                    result.append({
                        "timestamp": m.timestamp.isoformat(),
                        "depth": m.depth,
                        "diameter": m.diameter,
                        "operator": m.operator,
                        "is_qualified": m.is_qualified,
                        "deviation": m.deviation,
                        "source": "database"
                    })
                
                return result
                
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            self.logger.error(f"从数据库加载测量数据失败: {e}")
            return []
    
    def load_filesystem_measurements(self, hole_id: str, project_id: str) -> List[Dict]:
        """从文件系统加载测量数据"""
        try:
            csv_files = self.hybrid_manager.hole_manager.get_hole_measurements(project_id, hole_id)
            
            all_data = []
            for csv_file in csv_files:
                data = self.hybrid_manager.hole_manager.load_measurement_data(csv_file)
                if data:
                    # 添加来源标识
                    for record in data:
                        record["source"] = "filesystem"
                        record["file"] = os.path.basename(csv_file)
                    all_data.extend(data)
            
            return all_data
            
        except Exception as e:
            self.logger.error(f"从文件系统加载测量数据失败: {e}")
            return []
    
    def save_measurements_to_database(self, hole_id: str, project_id: str, 
                                    measurement_data: List[Dict]) -> bool:
        """保存测量数据到数据库"""
        try:
            session = self.db_manager.get_session()
            try:
                workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                if not workpiece:
                    return False
                
                hole = session.query(Hole).filter_by(
                    workpiece_id=workpiece.id, hole_id=hole_id
                ).first()
                if not hole:
                    return False
                
                for data in measurement_data:
                    # 计算偏差和合格性
                    diameter = float(data.get("diameter", 0))
                    deviation = abs(diameter - hole.target_diameter)
                    is_qualified = deviation <= hole.tolerance
                    
                    measurement = Measurement(
                        hole_id=hole.id,
                        depth=float(data.get("depth", 0)),
                        diameter=diameter,
                        operator=data.get("operator", "系统"),
                        is_qualified=is_qualified,
                        deviation=deviation,
                        timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now()
                    )
                    session.add(measurement)
                
                session.commit()
                return True
                
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            self.logger.error(f"保存测量数据到数据库失败: {e}")
            return False
    
    def update_hole_status(self, hole_id: str, project_id: str, status: str, reason: str) -> bool:
        """更新孔位状态"""
        try:
            # 更新文件系统状态
            fs_success = self.hybrid_manager.hole_manager.update_hole_status(
                project_id, hole_id, status, reason
            )
            
            # 更新数据库状态
            session = self.db_manager.get_session()
            try:
                workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                if workpiece:
                    hole = session.query(Hole).filter_by(
                        workpiece_id=workpiece.id, hole_id=hole_id
                    ).first()
                    if hole:
                        hole.status = status
                        hole.updated_at = datetime.now()
                        session.commit()
            finally:
                self.db_manager.close_session(session)
            
            return fs_success
            
        except Exception as e:
            self.logger.error(f"更新孔位状态失败: {e}")
            return False
    
    def update_measurement_statistics(self, hole_id: str, project_id: str, new_count: int) -> bool:
        """更新测量统计"""
        try:
            session = self.db_manager.get_session()
            try:
                workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                if workpiece:
                    hole = session.query(Hole).filter_by(
                        workpiece_id=workpiece.id, hole_id=hole_id
                    ).first()
                    if hole:
                        hole.measurement_count += new_count
                        session.commit()
                        return True
            finally:
                self.db_manager.close_session(session)
            
            return False
            
        except Exception as e:
            self.logger.error(f"更新测量统计失败: {e}")
            return False
    
    def deduplicate_measurements(self, measurements: List[Dict]) -> List[Dict]:
        """去重测量数据"""
        seen = set()
        unique_measurements = []
        
        for measurement in measurements:
            # 使用时间戳和深度作为唯一标识
            key = (measurement.get("timestamp", ""), measurement.get("depth", 0))
            if key not in seen:
                seen.add(key)
                unique_measurements.append(measurement)
        
        return unique_measurements
