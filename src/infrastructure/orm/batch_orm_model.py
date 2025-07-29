"""
批次ORM模型
用于数据库持久化的SQLAlchemy模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# 使用独立的Base，避免与旧模型耦合
Base = declarative_base()


class InspectionBatchORM(Base):
    """检测批次ORM模型"""
    __tablename__ = 'inspection_batches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(50), nullable=False, unique=True, comment='批次ID')
    product_id = Column(Integer, nullable=False, comment='产品ID')
    
    # 基本信息
    operator = Column(String(100), nullable=True, comment='操作员')
    equipment_id = Column(String(50), nullable=True, comment='设备ID')
    start_time = Column(DateTime, nullable=True, comment='开始时间')
    end_time = Column(DateTime, nullable=True, comment='结束时间')
    
    # 检测信息
    detection_number = Column(Integer, default=1, nullable=False, comment='检测次数')
    detection_type = Column(String(20), default='real', nullable=False, comment='检测类型')
    is_mock = Column(Boolean, default=False, comment='是否为模拟批次')
    pause_state = Column(Text, nullable=True, comment='暂停状态JSON')
    resume_count = Column(Integer, default=0, comment='恢复次数')
    
    # 检测统计
    total_holes = Column(Integer, default=0, comment='总孔数')
    completed_holes = Column(Integer, default=0, comment='完成孔数')
    qualified_holes = Column(Integer, default=0, comment='合格孔数')
    defective_holes = Column(Integer, default=0, comment='缺陷孔数')
    # 注意：以下字段在新架构中存在，但现有数据库中没有
    # blind_holes = Column(Integer, default=0, comment='盲孔数')
    # tie_rod_holes = Column(Integer, default=0, comment='拉杆孔数')
    
    # 统计指标
    overall_progress = Column(Float, default=0.0, comment='总体进度')
    qualification_rate = Column(Float, default=0.0, comment='合格率')
    
    # 状态和路径
    status = Column(String(20), default='pending', comment='批次状态')
    data_path = Column(String(500), nullable=True, comment='数据路径')
    description = Column(Text, nullable=True, comment='批次描述')
    
    # 新增路径字段
    batch_data_path = Column(String(500), nullable=True, comment='批次数据路径')
    hole_results_path = Column(String(500), nullable=True, comment='孔位结果路径')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')