"""
批次仓储实现
实现批次数据的持久化存储
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from src.core.domain.models.detection_batch import (
    DetectionBatch, BatchStatus, DetectionType, 
    DetectionProgress, DetectionState
)
from src.core.domain.repositories.batch_repository import IBatchRepository
from src.core.infrastructure.orm import Base, InspectionBatchORM
from src.core.data_path_manager import DataPathManager


class BatchRepositoryImpl(IBatchRepository):
    """批次仓储SQLAlchemy实现"""
    
    def __init__(self, db_path: str = None, path_manager: DataPathManager = None):
        """初始化仓储"""
        if db_path is None:
            # 使用项目根目录的Data/Databases
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            db_dir = os.path.join(project_root, 'Data', 'Databases')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'product_models.db')
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        self.path_manager = path_manager or DataPathManager()
    
    def save(self, batch: DetectionBatch) -> bool:
        """保存批次"""
        try:
            # 查找现有记录
            db_batch = self.session.query(InspectionBatchORM).filter_by(
                batch_id=batch.batch_id
            ).first()
            
            if db_batch is None:
                # 创建新记录
                db_batch = InspectionBatchORM(
                    batch_id=batch.batch_id,
                    product_id=batch.product_id,
                    detection_number=batch.detection_number,
                    detection_type=batch.detection_type.value,
                    is_mock=batch.is_mock,
                    status=batch.status.value,
                    operator=batch.operator,
                    equipment_id=batch.equipment_id,
                    description=batch.description,
                    created_at=batch.created_at,
                    data_path=batch.data_path
                )
                self.session.add(db_batch)
            else:
                # 更新现有记录
                db_batch.status = batch.status.value
                db_batch.start_time = batch.start_time
                db_batch.end_time = batch.end_time
                db_batch.description = batch.description
                
                # 更新进度
                db_batch.total_holes = batch.progress.total_holes
                db_batch.completed_holes = batch.progress.completed_holes
                db_batch.qualified_holes = batch.progress.qualified_holes
                db_batch.defective_holes = batch.progress.defective_holes
                db_batch.overall_progress = batch.progress.completion_rate
                db_batch.qualification_rate = batch.progress.qualification_rate
                
                # 更新状态
                db_batch.resume_count = batch.state.resume_count
                if batch.state.pause_time:
                    db_batch.pause_state = json.dumps({
                        'pause_time': batch.state.pause_time.isoformat(),
                        'detection_results': batch.state.detection_results,
                        'pending_holes': batch.state.pending_holes,
                        'simulation_params': batch.state.simulation_params
                    }, ensure_ascii=False)
            
            self.session.commit()
            return True
            
        except Exception as e:
            self.session.rollback()
            print(f"保存批次失败: {e}")
            return False
    
    def find_by_id(self, batch_id: str) -> Optional[DetectionBatch]:
        """根据ID查找批次"""
        db_batch = self.session.query(InspectionBatchORM).filter_by(
            batch_id=batch_id
        ).first()
        
        if db_batch:
            return self._to_domain_model(db_batch)
        return None
    
    def find_by_product(self, product_id: int, detection_type: str = None) -> List[DetectionBatch]:
        """根据产品查找批次"""
        # 防御性编程：确保product_id是整数
        if hasattr(product_id, 'id'):
            product_id = product_id.id
        
        query = self.session.query(InspectionBatchORM).filter_by(product_id=product_id)
        
        if detection_type:
            query = query.filter_by(detection_type=detection_type)
        
        db_batches = query.order_by(InspectionBatchORM.created_at.desc()).all()
        return [self._to_domain_model(db) for db in db_batches]
    
    def find_resumable(self, product_id: int, detection_type: str) -> Optional[DetectionBatch]:
        """查找可恢复的批次"""
        # 防御性编程：确保product_id是整数
        if hasattr(product_id, 'id'):
            product_id = product_id.id
        
        db_batch = self.session.query(InspectionBatchORM).filter_by(
            product_id=product_id,
            status='paused',
            detection_type=detection_type
        ).order_by(InspectionBatchORM.created_at.desc()).first()
        
        if db_batch:
            return self._to_domain_model(db_batch)
        return None
    
    def get_next_detection_number(self, product_id: int) -> int:
        """获取下一个检测序号"""
        # 防御性编程：确保product_id是整数
        if hasattr(product_id, 'id'):
            product_id = product_id.id
        
        max_number = self.session.query(func.max(InspectionBatchORM.detection_number))\
            .filter_by(product_id=product_id)\
            .scalar()
        
        return (max_number or 0) + 1
    
    def delete(self, batch_id: str) -> bool:
        """删除批次"""
        try:
            db_batch = self.session.query(InspectionBatchORM).filter_by(
                batch_id=batch_id
            ).first()
            
            if db_batch:
                self.session.delete(db_batch)
                self.session.commit()
                return True
            return False
            
        except Exception as e:
            self.session.rollback()
            print(f"删除批次失败: {e}")
            return False
    
    def update_progress(self, batch_id: str, progress: Dict[str, Any]) -> bool:
        """更新进度"""
        try:
            db_batch = self.session.query(InspectionBatchORM).filter_by(
                batch_id=batch_id
            ).first()
            
            if db_batch:
                if 'total_holes' in progress:
                    db_batch.total_holes = progress['total_holes']
                if 'completed_holes' in progress:
                    db_batch.completed_holes = progress['completed_holes']
                if 'qualified_holes' in progress:
                    db_batch.qualified_holes = progress['qualified_holes']
                if 'defective_holes' in progress:
                    db_batch.defective_holes = progress['defective_holes']
                
                # 计算进度
                if db_batch.total_holes > 0:
                    db_batch.overall_progress = (db_batch.completed_holes / db_batch.total_holes) * 100
                
                # 计算合格率
                if db_batch.completed_holes > 0:
                    db_batch.qualification_rate = (db_batch.qualified_holes / db_batch.completed_holes) * 100
                
                self.session.commit()
                return True
            return False
            
        except Exception as e:
            self.session.rollback()
            print(f"更新进度失败: {e}")
            return False
    
    def save_state(self, batch_id: str, state: Dict[str, Any]) -> bool:
        """保存状态到文件"""
        try:
            batch = self.find_by_id(batch_id)
            if not batch or not batch.data_path:
                return False
            
            state_path = os.path.join(batch.data_path, 'detection_state.json')
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"保存状态失败: {e}")
            return False
    
    def load_state(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """从文件加载状态"""
        try:
            batch = self.find_by_id(batch_id)
            if not batch or not batch.data_path:
                return None
            
            state_path = os.path.join(batch.data_path, 'detection_state.json')
            if os.path.exists(state_path):
                with open(state_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            print(f"加载状态失败: {e}")
            return None
    
    def _to_domain_model(self, db_batch: InspectionBatchORM) -> DetectionBatch:
        """转换为领域模型"""
        # 解析进度
        progress = DetectionProgress(
            current_index=0,  # 需要从状态中恢复
            total_holes=db_batch.total_holes,
            completed_holes=db_batch.completed_holes,
            qualified_holes=db_batch.qualified_holes,
            defective_holes=db_batch.defective_holes
        )
        
        # 解析状态
        state = DetectionState()
        if db_batch.pause_state:
            try:
                pause_data = json.loads(db_batch.pause_state)
                if pause_data.get('pause_time'):
                    state.pause_time = datetime.fromisoformat(pause_data['pause_time'])
                state.detection_results = pause_data.get('detection_results', {})
                state.pending_holes = pause_data.get('pending_holes', [])
                state.simulation_params = pause_data.get('simulation_params', {})
            except Exception:
                pass
        
        state.resume_count = db_batch.resume_count
        
        # 创建领域模型
        return DetectionBatch(
            batch_id=db_batch.batch_id,
            product_id=db_batch.product_id,
            detection_number=db_batch.detection_number,
            detection_type=DetectionType(db_batch.detection_type),
            status=BatchStatus(db_batch.status),
            operator=db_batch.operator,
            equipment_id=db_batch.equipment_id,
            description=db_batch.description,
            created_at=db_batch.created_at,
            start_time=db_batch.start_time,
            end_time=db_batch.end_time,
            progress=progress,
            state=state,
            data_path=db_batch.data_path
        )
    
    def close(self):
        """关闭连接"""
        self.session.close()