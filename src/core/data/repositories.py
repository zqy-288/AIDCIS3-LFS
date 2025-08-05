"""
数据仓库模块
提供各种数据实体的仓库类
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .data_access_layer import data_access_layer


class BaseRepository:
    """基础仓库类"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.dal = data_access_layer
        self.logger = logging.getLogger(__name__)


class WorkpieceRepository(BaseRepository):
    """工件仓库"""
    
    def __init__(self):
        super().__init__('workpieces')
    
    def create(self, name: str, description: str = None) -> Optional[int]:
        """创建工件"""
        try:
            query = """
                INSERT INTO workpieces (name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """
            now = datetime.now()
            params = (name, description, now, now)
            
            with self.dal.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"创建工件失败: {e}")
            return None
    
    def get_by_id(self, workpiece_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取工件"""
        query = "SELECT * FROM workpieces WHERE id = ?"
        results = self.dal.execute_query(query, (workpiece_id,))
        return results[0] if results else None
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取工件"""
        query = "SELECT * FROM workpieces WHERE name = ?"
        results = self.dal.execute_query(query, (name,))
        return results[0] if results else None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """获取所有工件"""
        query = "SELECT * FROM workpieces ORDER BY created_at DESC"
        return self.dal.execute_query(query)
    
    def update(self, workpiece_id: int, name: str = None, description: str = None) -> bool:
        """更新工件"""
        try:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if not updates:
                return True
            
            updates.append("updated_at = ?")
            params.append(datetime.now())
            params.append(workpiece_id)
            
            query = f"UPDATE workpieces SET {', '.join(updates)} WHERE id = ?"
            return self.dal.execute_non_query(query, tuple(params)) > 0
        except Exception as e:
            self.logger.error(f"更新工件失败: {e}")
            return False
    
    def delete(self, workpiece_id: int) -> bool:
        """删除工件"""
        try:
            query = "DELETE FROM workpieces WHERE id = ?"
            return self.dal.execute_non_query(query, (workpiece_id,)) > 0
        except Exception as e:
            self.logger.error(f"删除工件失败: {e}")
            return False


class HoleRepository(BaseRepository):
    """孔位仓库"""
    
    def __init__(self):
        super().__init__('holes')
    
    def create(self, workpiece_id: int, hole_id: str, x: float, y: float, 
               diameter: float = None, status: str = 'unknown') -> Optional[int]:
        """创建孔位"""
        try:
            query = """
                INSERT INTO holes (workpiece_id, hole_id, x, y, diameter, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            now = datetime.now()
            params = (workpiece_id, hole_id, x, y, diameter, status, now, now)
            
            with self.dal.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"创建孔位失败: {e}")
            return None
    
    def get_by_id(self, hole_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取孔位"""
        query = "SELECT * FROM holes WHERE id = ?"
        results = self.dal.execute_query(query, (hole_id,))
        return results[0] if results else None
    
    def get_by_hole_id(self, hole_id: str, workpiece_id: int = None) -> Optional[Dict[str, Any]]:
        """根据孔位ID获取孔位"""
        if workpiece_id:
            query = "SELECT * FROM holes WHERE hole_id = ? AND workpiece_id = ?"
            params = (hole_id, workpiece_id)
        else:
            query = "SELECT * FROM holes WHERE hole_id = ?"
            params = (hole_id,)
        
        results = self.dal.execute_query(query, params)
        return results[0] if results else None
    
    def get_by_workpiece(self, workpiece_id: int) -> List[Dict[str, Any]]:
        """获取工件的所有孔位"""
        query = "SELECT * FROM holes WHERE workpiece_id = ? ORDER BY hole_id"
        return self.dal.execute_query(query, (workpiece_id,))
    
    def update_status(self, hole_id: int, status: str) -> bool:
        """更新孔位状态"""
        try:
            query = "UPDATE holes SET status = ?, updated_at = ? WHERE id = ?"
            params = (status, datetime.now(), hole_id)
            return self.dal.execute_non_query(query, params) > 0
        except Exception as e:
            self.logger.error(f"更新孔位状态失败: {e}")
            return False
    
    def update_position(self, hole_id: int, x: float, y: float) -> bool:
        """更新孔位位置"""
        try:
            query = "UPDATE holes SET x = ?, y = ?, updated_at = ? WHERE id = ?"
            params = (x, y, datetime.now(), hole_id)
            return self.dal.execute_non_query(query, params) > 0
        except Exception as e:
            self.logger.error(f"更新孔位位置失败: {e}")
            return False
    
    def delete(self, hole_id: int) -> bool:
        """删除孔位"""
        try:
            query = "DELETE FROM holes WHERE id = ?"
            return self.dal.execute_non_query(query, (hole_id,)) > 0
        except Exception as e:
            self.logger.error(f"删除孔位失败: {e}")
            return False


class MeasurementRepository(BaseRepository):
    """测量仓库"""
    
    def __init__(self):
        super().__init__('measurements')
    
    def create(self, hole_id: int, measurement_type: str, value: float, unit: str = None) -> Optional[int]:
        """创建测量记录"""
        try:
            query = """
                INSERT INTO measurements (hole_id, measurement_type, value, unit, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (hole_id, measurement_type, value, unit, datetime.now())
            
            with self.dal.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"创建测量记录失败: {e}")
            return None
    
    def get_by_hole(self, hole_id: int) -> List[Dict[str, Any]]:
        """获取孔位的所有测量记录"""
        query = "SELECT * FROM measurements WHERE hole_id = ? ORDER BY timestamp DESC"
        return self.dal.execute_query(query, (hole_id,))
    
    def get_by_type(self, hole_id: int, measurement_type: str) -> List[Dict[str, Any]]:
        """获取特定类型的测量记录"""
        query = "SELECT * FROM measurements WHERE hole_id = ? AND measurement_type = ? ORDER BY timestamp DESC"
        return self.dal.execute_query(query, (hole_id, measurement_type))
    
    def get_latest(self, hole_id: int, measurement_type: str = None) -> Optional[Dict[str, Any]]:
        """获取最新的测量记录"""
        if measurement_type:
            query = "SELECT * FROM measurements WHERE hole_id = ? AND measurement_type = ? ORDER BY timestamp DESC LIMIT 1"
            params = (hole_id, measurement_type)
        else:
            query = "SELECT * FROM measurements WHERE hole_id = ? ORDER BY timestamp DESC LIMIT 1"
            params = (hole_id,)
        
        results = self.dal.execute_query(query, params)
        return results[0] if results else None
    
    def delete(self, measurement_id: int) -> bool:
        """删除测量记录"""
        try:
            query = "DELETE FROM measurements WHERE id = ?"
            return self.dal.execute_non_query(query, (measurement_id,)) > 0
        except Exception as e:
            self.logger.error(f"删除测量记录失败: {e}")
            return False


# 创建全局仓库实例
workpiece_repository = WorkpieceRepository()
hole_repository = HoleRepository()
measurement_repository = MeasurementRepository()
