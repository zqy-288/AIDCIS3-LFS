"""
ORM模型层
包含所有数据库持久化相关的SQLAlchemy模型
"""

from .batch_orm_model import Base, InspectionBatchORM

__all__ = ['Base', 'InspectionBatchORM']