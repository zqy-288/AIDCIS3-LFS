"""
[DEPRECATED] 检测批次数据模型 - 已废弃
管理产品检测批次的创建、查询、更新等操作

⚠️ 此文件已被重构后的新架构替代：
- 领域模型: /src/domain/models/detection_batch.py
- 仓储接口: /src/domain/repositories/batch_repository.py  
- 仓储实现: /src/infrastructure/repositories/batch_repository_impl.py
- 批次服务: /src/domain/services/batch_service.py

请使用新的架构实现，本文件仅保留用于向后兼容。
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from datetime import datetime
from typing import List, Optional, Dict
import json
import os

# 使用与产品模型相同的Base
from models.product_model import Base, get_product_manager
from models.data_path_manager import get_data_path_manager


class InspectionBatch(Base):
    """检测批次数据模型"""
    __tablename__ = 'inspection_batches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), nullable=False, unique=True, comment='批次ID (YYYYMMDD_HHMMSS)')
    product_id = Column(Integer, ForeignKey('product_models.id'), nullable=False, comment='关联的产品ID')
    
    # 基本信息
    operator = Column(String(100), nullable=True, comment='操作员')
    equipment_id = Column(String(50), nullable=True, comment='设备ID')
    start_time = Column(DateTime, default=datetime.now, comment='开始时间')
    end_time = Column(DateTime, nullable=True, comment='结束时间')
    
    # 新增字段：支持检测次数和类型
    detection_number = Column(Integer, default=1, nullable=False, comment='该产品的第几次检测')
    detection_type = Column(String(20), default='real', nullable=False, comment='检测类型: real/mock')
    is_mock = Column(Boolean, default=False, comment='是否为模拟批次')
    pause_state = Column(Text, nullable=True, comment='暂停状态JSON')
    resume_count = Column(Integer, default=0, comment='恢复次数')
    
    # 检测统计
    total_holes = Column(Integer, default=0, comment='总孔数')
    completed_holes = Column(Integer, default=0, comment='已完成孔数')
    qualified_holes = Column(Integer, default=0, comment='合格孔数')
    defective_holes = Column(Integer, default=0, comment='异常孔数')
    
    # 进度和状态
    overall_progress = Column(Float, default=0.0, comment='整体进度百分比')
    qualification_rate = Column(Float, default=0.0, comment='合格率百分比')
    status = Column(String(20), default='pending', comment='状态: pending/running/completed/failed')
    
    # 路径和描述
    data_path = Column(String(500), nullable=True, comment='数据存储路径')
    description = Column(Text, nullable=True, comment='检测批次描述')
    
    # 新增：支持新目录结构
    batch_data_path = Column(String(500), nullable=True, comment='批次数据存储路径')
    hole_results_path = Column(String(500), nullable=True, comment='孔位结果存储路径')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<InspectionBatch(batch_id='{self.batch_id}', product_id={self.product_id}, status='{self.status}')>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'product_id': self.product_id,
            'operator': self.operator,
            'equipment_id': self.equipment_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_holes': self.total_holes,
            'completed_holes': self.completed_holes,
            'qualified_holes': self.qualified_holes,
            'defective_holes': self.defective_holes,
            'overall_progress': self.overall_progress,
            'qualification_rate': self.qualification_rate,
            'status': self.status,
            'data_path': self.data_path,
            'description': self.description,
            'batch_data_path': self.batch_data_path,
            'hole_results_path': self.hole_results_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def duration(self) -> Optional[float]:
        """获取检测持续时间（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.status == 'completed'
    
    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.status == 'running'


class InspectionBatchManager:
    """检测批次管理器"""
    
    def __init__(self, db_path=None, product_manager=None, path_manager=None):
        if db_path is None:
            # 使用与产品模型相同的数据库
            db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'product_models.db')
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        self.path_manager = path_manager if path_manager else get_data_path_manager()
        self._product_manager = product_manager  # 可选的产品管理器实例
    
    def _get_next_detection_number(self, product_id: int) -> int:
        """获取产品的下一个检测次数"""
        # 防御性编程：确保product_id是整数
        if hasattr(product_id, 'id'):
            product_id = product_id.id
        
        # 查询该产品的最大检测次数
        max_number = self.session.query(func.max(InspectionBatch.detection_number))\
            .filter_by(product_id=product_id)\
            .scalar()
        
        return (max_number or 0) + 1
    
    def create_batch(self, product_id: int, operator: str = None, 
                    equipment_id: str = None, description: str = None,
                    is_mock: bool = False) -> InspectionBatch:
        """创建新的检测批次"""
        # 防御性编程：确保product_id是整数，而不是ProductModel对象
        if hasattr(product_id, 'id'):
            # 如果传入的是ProductModel对象，提取其ID
            print(f"警告：create_batch接收到ProductModel对象而不是ID，自动转换")
            product_id = product_id.id
        
        # 获取产品信息
        if self._product_manager:
            product = self._product_manager.get_product_by_id(product_id)
        else:
            product_manager = get_product_manager()
            product = product_manager.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"产品 ID {product_id} 不存在")
        
        # 获取该产品的检测次数
        detection_number = self._get_next_detection_number(product_id)
        
        # 生成批次ID（包含检测次数和类型标识）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        detection_type = 'mock' if is_mock else 'real'
        mock_suffix = '_MOCK' if is_mock else ''
        batch_id = f"{product.model_name}_检测{detection_number:03d}_{timestamp}{mock_suffix}"
        
        # 创建新的目录结构
        self.path_manager.create_inspection_structure(product.model_name, batch_id)
        data_path = self.path_manager.get_inspection_batch_path(product.model_name, batch_id)
        
        # 新增：支持新目录结构的路径
        batch_data_path = self.path_manager.get_data_batches_dir(product.model_name, batch_id)
        hole_results_path = self.path_manager.get_hole_results_dir(product.model_name, batch_id)
        
        # 创建批次记录
        batch = InspectionBatch(
            batch_id=batch_id,
            product_id=product_id,
            operator=operator,
            equipment_id=equipment_id,
            description=description,
            data_path=data_path,
            batch_data_path=batch_data_path,
            hole_results_path=hole_results_path,
            status='pending',
            detection_number=detection_number,
            detection_type=detection_type,
            is_mock=is_mock
        )
        
        self.session.add(batch)
        self.session.commit()
        
        # 创建检测信息文件
        self._create_inspection_info_file(batch, product)
        
        return batch
    
    def get_batch_by_id(self, batch_id: str) -> Optional[InspectionBatch]:
        """根据批次ID获取检测批次"""
        return self.session.query(InspectionBatch).filter(InspectionBatch.batch_id == batch_id).first()
    
    def get_product_batches(self, product_id: int) -> List[InspectionBatch]:
        """获取产品的所有批次"""
        return self.session.query(InspectionBatch)\
            .filter_by(product_id=product_id)\
            .order_by(InspectionBatch.created_at.desc())\
            .all()
    
    def get_batch_by_pk(self, pk: int) -> Optional[InspectionBatch]:
        """根据主键获取检测批次"""
        return self.session.query(InspectionBatch).filter(InspectionBatch.id == pk).first()
    
    def get_batches_by_product(self, product_id: int) -> List[InspectionBatch]:
        """获取指定产品的所有检测批次"""
        # 防御性编程：确保product_id是整数
        if hasattr(product_id, 'id'):
            product_id = product_id.id
        
        return self.session.query(InspectionBatch).filter(
            InspectionBatch.product_id == product_id
        ).order_by(InspectionBatch.created_at.desc()).all()
    
    def get_active_batches(self) -> List[InspectionBatch]:
        """获取所有活跃的检测批次（运行中或待处理）"""
        return self.session.query(InspectionBatch).filter(
            InspectionBatch.status.in_(['pending', 'running'])
        ).order_by(InspectionBatch.created_at.desc()).all()
    
    def get_all_batches(self, limit: int = None) -> List[InspectionBatch]:
        """获取所有检测批次"""
        query = self.session.query(InspectionBatch).order_by(InspectionBatch.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def start_batch(self, batch_id: str) -> bool:
        """开始检测批次"""
        batch = self.get_batch_by_id(batch_id)
        if not batch:
            return False
        
        batch.status = 'running'
        batch.start_time = datetime.now()
        self.session.commit()
        
        # 更新检测信息文件
        self._update_inspection_info_file(batch)
        return True
    
    def complete_batch(self, batch_id: str) -> bool:
        """完成检测批次"""
        batch = self.get_batch_by_id(batch_id)
        if not batch:
            return False
        
        batch.status = 'completed'
        batch.end_time = datetime.now()
        batch.overall_progress = 100.0
        
        # 计算合格率
        if batch.completed_holes > 0:
            batch.qualification_rate = (batch.qualified_holes / batch.completed_holes) * 100
        
        self.session.commit()
        
        # 更新检测信息文件和创建汇总文件
        self._update_inspection_info_file(batch)
        self._create_summary_file(batch)
        return True
    
    def update_batch_progress(self, batch_id: str, total_holes: int = None,
                            completed_holes: int = None, qualified_holes: int = None,
                            defective_holes: int = None) -> bool:
        """更新检测批次进度"""
        batch = self.get_batch_by_id(batch_id)
        if not batch:
            return False
        
        if total_holes is not None:
            batch.total_holes = total_holes
        if completed_holes is not None:
            batch.completed_holes = completed_holes
        if qualified_holes is not None:
            batch.qualified_holes = qualified_holes
        if defective_holes is not None:
            batch.defective_holes = defective_holes
        
        # 计算进度
        if batch.total_holes > 0:
            batch.overall_progress = (batch.completed_holes / batch.total_holes) * 100
        
        # 计算合格率
        if batch.completed_holes > 0:
            batch.qualification_rate = (batch.qualified_holes / batch.completed_holes) * 100
        
        batch.updated_at = datetime.now()
        self.session.commit()
        
        # 更新汇总文件
        self._update_summary_file(batch)
        return True
    
    def delete_batch(self, batch_id: str, delete_files: bool = False) -> bool:
        """删除检测批次"""
        batch = self.get_batch_by_id(batch_id)
        if not batch:
            return False
        
        # 可选择删除相关文件
        if delete_files and batch.data_path and os.path.exists(batch.data_path):
            import shutil
            try:
                shutil.rmtree(batch.data_path)
            except Exception as e:
                print(f"删除批次文件失败: {e}")
        
        self.session.delete(batch)
        self.session.commit()
        return True
    
    def _create_inspection_info_file(self, batch: InspectionBatch, product):
        """创建检测信息文件"""
        if not batch.data_path:
            return
        
        info_path = self.path_manager.get_batch_info_path(product.model_name, batch.batch_id)
        
        info_data = {
            'batch_id': batch.batch_id,
            'product_id': product.model_name,
            'product_name': product.model_name,
            'start_time': batch.start_time.isoformat() if batch.start_time else None,
            'end_time': batch.end_time.isoformat() if batch.end_time else None,
            'operator': batch.operator,
            'equipment_id': batch.equipment_id,
            'total_holes': batch.total_holes,
            'status': batch.status,
            'description': batch.description,
            'created_at': batch.created_at.isoformat(),
            'updated_at': batch.updated_at.isoformat()
        }
        
        try:
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"创建检测信息文件失败: {e}")
    
    def _update_inspection_info_file(self, batch: InspectionBatch):
        """更新检测信息文件"""
        if not batch.data_path:
            return
        
        if self._product_manager:
            product = self._product_manager.get_product_by_id(batch.product_id)
        else:
            product_manager = get_product_manager()
            product = product_manager.get_product_by_id(batch.product_id)
        if not product:
            return
        
        info_path = self.path_manager.get_batch_info_path(product.model_name, batch.batch_id)
        
        info_data = {
            'batch_id': batch.batch_id,
            'product_id': product.model_name,
            'product_name': product.model_name,
            'start_time': batch.start_time.isoformat() if batch.start_time else None,
            'end_time': batch.end_time.isoformat() if batch.end_time else None,
            'operator': batch.operator,
            'equipment_id': batch.equipment_id,
            'total_holes': batch.total_holes,
            'status': batch.status,
            'description': batch.description,
            'overall_progress': batch.overall_progress,
            'qualification_rate': batch.qualification_rate,
            'created_at': batch.created_at.isoformat(),
            'updated_at': batch.updated_at.isoformat()
        }
        
        try:
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"更新检测信息文件失败: {e}")
    
    def _create_summary_file(self, batch: InspectionBatch):
        """创建检测汇总文件"""
        self._update_summary_file(batch)
    
    def _update_summary_file(self, batch: InspectionBatch):
        """更新检测汇总文件"""
        if not batch.data_path:
            return
        
        if self._product_manager:
            product = self._product_manager.get_product_by_id(batch.product_id)
        else:
            product_manager = get_product_manager()
            product = product_manager.get_product_by_id(batch.product_id)
        if not product:
            return
        
        summary_path = self.path_manager.get_batch_summary_path(product.model_name, batch.batch_id)
        
        # 这里可以扩展为包含扇形区域的详细统计
        summary_data = {
            'batch_id': batch.batch_id,
            'total_holes': batch.total_holes,
            'completed_holes': batch.completed_holes,
            'qualified_holes': batch.qualified_holes,
            'defective_holes': batch.defective_holes,
            'overall_progress': batch.overall_progress,
            'qualification_rate': batch.qualification_rate,
            'sector_results': {
                # 这里可以添加扇形区域的详细统计
                # 需要与SectorManager集成
            },
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"更新汇总文件失败: {e}")
    
    def get_resumable_batch(self, product_id: int, is_mock: bool = False) -> Optional[InspectionBatch]:
        """获取可恢复的批次（最新的暂停状态批次）"""
        # 防御性编程：确保product_id是整数
        if hasattr(product_id, 'id'):
            product_id = product_id.id
        
        return self.session.query(InspectionBatch)\
            .filter_by(product_id=product_id, status='paused', is_mock=is_mock)\
            .order_by(InspectionBatch.created_at.desc())\
            .first()
    
    def pause_batch(self, batch_id: str, detection_state: dict) -> bool:
        """暂停批次并保存状态"""
        batch = self.get_batch_by_id(batch_id)
        if not batch:
            return False
            
        batch.status = 'paused'
        batch.pause_state = json.dumps(detection_state, ensure_ascii=False)
        self.session.commit()
        
        # 保存状态文件
        state_path = os.path.join(batch.data_path, 'detection_state.json')
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(detection_state, f, indent=2, ensure_ascii=False)
            
        return True
    
    def resume_batch(self, batch_id: str) -> Optional[dict]:
        """恢复批次并返回检测状态"""
        batch = self.get_batch_by_id(batch_id)
        if not batch or batch.status != 'paused':
            return None
            
        batch.status = 'running'
        batch.resume_count += 1
        self.session.commit()
        
        # 加载状态文件
        state_path = os.path.join(batch.data_path, 'detection_state.json')
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif batch.pause_state:
            return json.loads(batch.pause_state)
            
        return None
    
    def terminate_batch(self, batch_id: str) -> bool:
        """终止批次"""
        batch = self.get_batch_by_id(batch_id)
        if not batch:
            return False
            
        batch.status = 'terminated'
        batch.end_time = datetime.now()
        self.session.commit()
        return True
    
    def close(self):
        """关闭数据库连接"""
        self.session.close()


# 单例实例
_batch_manager = None


def get_batch_manager(db_path=None, product_manager=None, path_manager=None):
    """获取批次管理器单例"""
    global _batch_manager
    if _batch_manager is None:
        _batch_manager = InspectionBatchManager(db_path, product_manager, path_manager)
    return _batch_manager

def get_inspection_batch_manager():
    """获取检测批次管理器单例"""
    global _batch_manager
    if _batch_manager is None:
        _batch_manager = InspectionBatchManager()
    return _batch_manager