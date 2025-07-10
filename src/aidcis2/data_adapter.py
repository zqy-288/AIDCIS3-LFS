"""
数据转换适配器
在AIDCIS2的HoleData模型与现有数据库模型之间进行转换
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from modules.models import Hole, Workpiece, Measurement


class DataAdapter:
    """数据转换适配器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 状态映射表：AIDCIS2状态 -> 数据库状态
        self.status_mapping = {
            HoleStatus.PENDING: 'not_detected',
            HoleStatus.QUALIFIED: 'qualified',
            HoleStatus.DEFECTIVE: 'defective',
            HoleStatus.BLIND: 'blind',
            HoleStatus.TIE_ROD: 'tie_rod',
            HoleStatus.PROCESSING: 'processing'
        }
        
        # 反向状态映射表：数据库状态 -> AIDCIS2状态
        self.reverse_status_mapping = {v: k for k, v in self.status_mapping.items()}
    
    def hole_data_to_db_model(self, hole_data: HoleData, workpiece_id: int) -> Hole:
        """
        将HoleData转换为数据库Hole模型
        
        Args:
            hole_data: AIDCIS2孔位数据
            workpiece_id: 工件ID
            
        Returns:
            Hole: 数据库孔位模型
        """
        try:
            # 计算目标直径（从半径转换）
            target_diameter = hole_data.radius * 2
            
            # 默认公差值（可以从metadata中获取或使用默认值）
            tolerance = hole_data.metadata.get('tolerance', 0.1) if hole_data.metadata else 0.1
            
            # 转换状态
            db_status = self.status_mapping.get(hole_data.status, 'not_detected')
            
            hole = Hole(
                hole_id=hole_data.hole_id,
                workpiece_id=workpiece_id,
                position_x=hole_data.center_x,
                position_y=hole_data.center_y,
                target_diameter=target_diameter,
                tolerance=tolerance,
                status=db_status,
                created_at=datetime.now()
            )
            
            self.logger.debug(f"转换HoleData到数据库模型: {hole_data.hole_id}")
            return hole
            
        except Exception as e:
            self.logger.error(f"转换HoleData到数据库模型失败: {e}")
            raise
    
    def db_model_to_hole_data(self, hole: Hole) -> HoleData:
        """
        将数据库Hole模型转换为HoleData
        
        Args:
            hole: 数据库孔位模型
            
        Returns:
            HoleData: AIDCIS2孔位数据
        """
        try:
            # 计算半径（从直径转换）
            radius = hole.target_diameter / 2
            
            # 转换状态
            aidcis2_status = self.reverse_status_mapping.get(hole.status, HoleStatus.PENDING)
            
            # 构建元数据
            metadata = {
                'db_id': hole.id,
                'workpiece_id': hole.workpiece_id,
                'tolerance': hole.tolerance,
                'created_at': hole.created_at.isoformat() if hole.created_at else None
            }
            
            hole_data = HoleData(
                hole_id=hole.hole_id,
                center_x=hole.position_x or 0.0,
                center_y=hole.position_y or 0.0,
                radius=radius,
                status=aidcis2_status,
                layer="0",  # 默认图层
                metadata=metadata
            )
            
            self.logger.debug(f"转换数据库模型到HoleData: {hole.hole_id}")
            return hole_data
            
        except Exception as e:
            self.logger.error(f"转换数据库模型到HoleData失败: {e}")
            raise
    
    def hole_collection_to_db_models(self, hole_collection: HoleCollection, workpiece_id: int) -> List[Hole]:
        """
        将HoleCollection转换为数据库Hole模型列表
        
        Args:
            hole_collection: AIDCIS2孔位集合
            workpiece_id: 工件ID
            
        Returns:
            List[Hole]: 数据库孔位模型列表
        """
        db_holes = []
        
        for hole_data in hole_collection:
            try:
                db_hole = self.hole_data_to_db_model(hole_data, workpiece_id)
                db_holes.append(db_hole)
            except Exception as e:
                self.logger.error(f"转换孔位 {hole_data.hole_id} 失败: {e}")
                continue
        
        self.logger.info(f"成功转换 {len(db_holes)}/{len(hole_collection)} 个孔位到数据库模型")
        return db_holes
    
    def db_models_to_hole_collection(self, holes: List[Hole], metadata: Optional[Dict] = None) -> HoleCollection:
        """
        将数据库Hole模型列表转换为HoleCollection
        
        Args:
            holes: 数据库孔位模型列表
            metadata: 集合元数据
            
        Returns:
            HoleCollection: AIDCIS2孔位集合
        """
        hole_data_dict = {}
        
        for hole in holes:
            try:
                hole_data = self.db_model_to_hole_data(hole)
                hole_data_dict[hole_data.hole_id] = hole_data
            except Exception as e:
                self.logger.error(f"转换数据库孔位 {hole.hole_id} 失败: {e}")
                continue
        
        # 构建集合元数据
        collection_metadata = metadata or {}
        collection_metadata.update({
            'conversion_timestamp': datetime.now().isoformat(),
            'source': 'database',
            'total_db_holes': len(holes),
            'converted_holes': len(hole_data_dict)
        })
        
        hole_collection = HoleCollection(
            holes=hole_data_dict,
            metadata=collection_metadata
        )
        
        self.logger.info(f"成功转换 {len(hole_data_dict)}/{len(holes)} 个数据库孔位到HoleCollection")
        return hole_collection
    
    def sync_status_to_database(self, hole_data: HoleData, db_session) -> bool:
        """
        将HoleData的状态同步到数据库
        
        Args:
            hole_data: AIDCIS2孔位数据
            db_session: 数据库会话
            
        Returns:
            bool: 同步是否成功
        """
        try:
            # 查找对应的数据库记录
            db_hole = db_session.query(Hole).filter_by(hole_id=hole_data.hole_id).first()
            
            if not db_hole:
                self.logger.warning(f"数据库中未找到孔位: {hole_data.hole_id}")
                return False
            
            # 更新状态
            new_status = self.status_mapping.get(hole_data.status, 'not_detected')
            db_hole.status = new_status
            
            # 更新坐标（如果有变化）
            if hole_data.center_x != db_hole.position_x or hole_data.center_y != db_hole.position_y:
                db_hole.position_x = hole_data.center_x
                db_hole.position_y = hole_data.center_y
            
            # 更新目标直径（如果有变化）
            new_diameter = hole_data.radius * 2
            if abs(new_diameter - db_hole.target_diameter) > 0.001:
                db_hole.target_diameter = new_diameter
            
            db_session.commit()
            self.logger.debug(f"成功同步孔位状态到数据库: {hole_data.hole_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"同步孔位状态到数据库失败: {e}")
            db_session.rollback()
            return False
    
    def batch_sync_status_to_database(self, hole_collection: HoleCollection, db_session) -> int:
        """
        批量同步HoleCollection状态到数据库
        
        Args:
            hole_collection: AIDCIS2孔位集合
            db_session: 数据库会话
            
        Returns:
            int: 成功同步的数量
        """
        success_count = 0
        
        for hole_data in hole_collection:
            if self.sync_status_to_database(hole_data, db_session):
                success_count += 1
        
        self.logger.info(f"批量同步完成，成功同步 {success_count}/{len(hole_collection)} 个孔位状态")
        return success_count
    
    def create_measurement_from_hole_data(self, hole_data: HoleData, measurement_data: Dict) -> Measurement:
        """
        从HoleData创建测量记录
        
        Args:
            hole_data: AIDCIS2孔位数据
            measurement_data: 测量数据字典
            
        Returns:
            Measurement: 测量记录
        """
        try:
            # 获取数据库中的孔位ID
            db_hole_id = hole_data.metadata.get('db_id') if hole_data.metadata else None
            
            if not db_hole_id:
                raise ValueError(f"孔位 {hole_data.hole_id} 缺少数据库ID")
            
            measurement = Measurement(
                hole_id=db_hole_id,
                depth=measurement_data.get('depth', 0.0),
                diameter=measurement_data.get('diameter', hole_data.radius * 2),
                timestamp=datetime.now(),
                operator=measurement_data.get('operator', 'system'),
                is_qualified=measurement_data.get('is_qualified', True),
                deviation=measurement_data.get('deviation', 0.0)
            )
            
            self.logger.debug(f"创建测量记录: {hole_data.hole_id}")
            return measurement
            
        except Exception as e:
            self.logger.error(f"创建测量记录失败: {e}")
            raise
    
    def validate_conversion(self, original: HoleData, converted: Hole, workpiece_id: int) -> bool:
        """
        验证转换的正确性
        
        Args:
            original: 原始HoleData
            converted: 转换后的Hole模型
            workpiece_id: 工件ID
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 验证基本字段
            if original.hole_id != converted.hole_id:
                return False
            
            if original.center_x != converted.position_x:
                return False
            
            if original.center_y != converted.position_y:
                return False
            
            if abs(original.radius * 2 - converted.target_diameter) > 0.001:
                return False
            
            if converted.workpiece_id != workpiece_id:
                return False
            
            # 验证状态映射
            expected_status = self.status_mapping.get(original.status)
            if converted.status != expected_status:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证转换失败: {e}")
            return False
