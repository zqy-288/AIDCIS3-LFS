"""
数据库模型定义
使用SQLAlchemy ORM定义数据表结构
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import ForeignKey
import json

Base = declarative_base()


class Workpiece(Base):
    """工件表 - 扩展支持优先级3数据管理"""
    __tablename__ = 'workpieces'

    id = Column(Integer, primary_key=True)
    workpiece_id = Column(String(50), unique=True, nullable=False)  # 工件ID
    name = Column(String(100), nullable=False)  # 工件名称
    type = Column(String(50), nullable=False)   # 工件类型
    material = Column(String(50))               # 材料
    dxf_file_path = Column(String(255))         # DXF文件路径 (新增)
    project_data_path = Column(String(255))     # 项目数据目录路径 (新增)
    hole_count = Column(Integer, default=0)     # 孔位总数 (新增)
    completed_holes = Column(Integer, default=0)  # 已完成孔位数 (新增)
    status = Column(String(20), default='active')  # 项目状态 (新增)
    description = Column(Text)                   # 项目描述 (新增)
    version = Column(String(10), default='1.0')  # 数据版本 (新增)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联关系
    holes = relationship("Hole", back_populates="workpiece")


class Hole(Base):
    """孔表 - 扩展支持优先级3数据管理"""
    __tablename__ = 'holes'

    id = Column(Integer, primary_key=True)
    hole_id = Column(String(50), nullable=False)  # 孔ID (如H001)
    workpiece_id = Column(Integer, ForeignKey('workpieces.id'), nullable=False)
    position_x = Column(Float)  # X坐标
    position_y = Column(Float)  # Y坐标
    target_diameter = Column(Float, nullable=False)  # 目标直径
    tolerance = Column(Float, nullable=False)        # 公差
    depth = Column(Float)                           # 孔深度 (新增)
    file_system_path = Column(String(255))          # 文件系统路径 (新增)
    status = Column(String(20), default='pending')  # 检测状态 (修改默认值)
    last_measurement_at = Column(DateTime)          # 最后测量时间 (新增)
    measurement_count = Column(Integer, default=0)  # 测量次数 (新增)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 新增

    # 关联关系
    workpiece = relationship("Workpiece", back_populates="holes")
    measurements = relationship("Measurement", back_populates="hole")
    endoscope_images = relationship("EndoscopeImage", back_populates="hole")
    status_updates = relationship("HoleStatusUpdate", back_populates="hole")


class Measurement(Base):
    """测量数据表"""
    __tablename__ = 'measurements'
    
    id = Column(Integer, primary_key=True)
    hole_id = Column(Integer, ForeignKey('holes.id'), nullable=False)
    depth = Column(Float, nullable=False)      # 深度 (mm)
    diameter = Column(Float, nullable=False)   # 直径 (mm)
    timestamp = Column(DateTime, default=datetime.now)
    operator = Column(String(50))             # 操作员
    
    # 质量评估
    is_qualified = Column(Boolean)            # 是否合格
    deviation = Column(Float)                 # 偏差值
    
    # 关联关系
    hole = relationship("Hole", back_populates="measurements")


class EndoscopeImage(Base):
    """内窥镜图像表"""
    __tablename__ = 'endoscope_images'
    
    id = Column(Integer, primary_key=True)
    hole_id = Column(Integer, ForeignKey('holes.id'), nullable=False)
    image_path = Column(String(255), nullable=False)  # 图像文件路径
    depth_start = Column(Float)                       # 起始深度
    depth_end = Column(Float)                         # 结束深度
    image_type = Column(String(20), default='raw')    # 图像类型: raw, stitched, unwrapped
    timestamp = Column(DateTime, default=datetime.now)
    
    # 关联关系
    hole = relationship("Hole", back_populates="endoscope_images")
    annotations = relationship("Annotation", back_populates="image")


class Annotation(Base):
    """标注数据表"""
    __tablename__ = 'annotations'
    
    id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey('endoscope_images.id'), nullable=False)
    annotation_type = Column(String(50), nullable=False)  # 标注类型: bbox, polygon
    defect_type = Column(String(50), nullable=False)      # 缺陷类型: crack, corrosion, etc.
    coordinates = Column(Text, nullable=False)            # 坐标数据 (JSON格式)
    confidence = Column(Float, default=1.0)               # 置信度
    annotator = Column(String(50))                        # 标注员
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    image = relationship("EndoscopeImage", back_populates="annotations")
    
    def set_coordinates(self, coords):
        """设置坐标数据"""
        self.coordinates = json.dumps(coords)
        
    def get_coordinates(self):
        """获取坐标数据"""
        return json.loads(self.coordinates) if self.coordinates else []


class HoleStatusUpdate(Base):
    """孔位状态更新记录表 - 用于全景图同步"""
    __tablename__ = 'hole_status_updates'
    
    id = Column(Integer, primary_key=True)
    hole_id = Column(Integer, ForeignKey('holes.id'), nullable=False)
    old_status = Column(String(20))
    new_status = Column(String(20), nullable=False)
    update_timestamp = Column(DateTime, default=datetime.now)
    sync_to_panorama = Column(Boolean, default=False)  # 是否已同步到全景图
    sync_timestamp = Column(DateTime)                   # 同步时间
    update_source = Column(String(50))                  # 更新来源(detection/manual/import等)
    operator_id = Column(String(50))                    # 操作员
    batch_id = Column(String(50))                       # 批次ID，用于批量更新
    
    # 关联关系
    hole = relationship("Hole", back_populates="status_updates")


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_url="sqlite:///detection_system.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
        
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
        
    def close_session(self, session):
        """关闭数据库会话"""
        session.close()
        
    def create_sample_data(self):
        """创建示例数据"""
        session = self.get_session()
        try:
            # 检查是否已有数据
            if session.query(Workpiece).first():
                return
                
            # 创建工件
            workpiece = Workpiece(
                workpiece_id="WP-2024-001",
                name="管板工件",
                type="tube_plate",
                material="不锈钢"
            )
            session.add(workpiece)
            session.flush()  # 获取ID
            
            # 创建孔
            import numpy as np
            rows, cols = 6, 8
            start_x, start_y = -140, -100
            spacing_x, spacing_y = 40, 35
            
            hole_count = 1
            for row in range(rows):
                for col in range(cols):
                    x = start_x + col * spacing_x
                    y = start_y + row * spacing_y
                    hole_id = f"H{hole_count:03d}"
                    
                    hole = Hole(
                        hole_id=hole_id,
                        workpiece_id=workpiece.id,
                        position_x=x,
                        position_y=y,
                        target_diameter=25.0,
                        tolerance=0.1
                    )
                    session.add(hole)
                    hole_count += 1
                    
            session.commit()
            print("示例数据创建成功")
            
        except Exception as e:
            session.rollback()
            print(f"创建示例数据失败: {e}")
        finally:
            self.close_session(session)
            
    def add_measurement_data(self, hole_id, depth, diameter, operator="系统"):
        """添加测量数据"""
        session = self.get_session()
        try:
            # 查找孔
            hole = session.query(Hole).filter_by(hole_id=hole_id).first()
            if not hole:
                print(f"未找到孔 {hole_id}")
                return False
                
            # 计算偏差和合格性
            deviation = abs(diameter - hole.target_diameter)
            is_qualified = deviation <= hole.tolerance
            
            # 创建测量记录
            measurement = Measurement(
                hole_id=hole.id,
                depth=depth,
                diameter=diameter,
                operator=operator,
                is_qualified=is_qualified,
                deviation=deviation
            )
            session.add(measurement)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"添加测量数据失败: {e}")
            return False
        finally:
            self.close_session(session)
            
    def get_hole_measurements(self, hole_id):
        """获取孔的所有测量数据"""
        session = self.get_session()
        try:
            hole = session.query(Hole).filter_by(hole_id=hole_id).first()
            if not hole:
                return []
                
            measurements = session.query(Measurement).filter_by(hole_id=hole.id).order_by(Measurement.depth).all()
            
            # 转换为字典列表
            result = []
            for m in measurements:
                result.append({
                    'depth': m.depth,
                    'diameter': m.diameter,
                    'timestamp': m.timestamp,
                    'is_qualified': m.is_qualified,
                    'deviation': m.deviation,
                    'operator': m.operator
                })
            return result
            
        except Exception as e:
            print(f"获取测量数据失败: {e}")
            return []
        finally:
            self.close_session(session)
            
    def get_workpiece_holes(self, workpiece_id):
        """获取工件的所有孔"""
        session = self.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=workpiece_id).first()
            if not workpiece:
                return []
                
            holes = session.query(Hole).filter_by(workpiece_id=workpiece.id).all()
            
            result = []
            for hole in holes:
                result.append({
                    'hole_id': hole.hole_id,
                    'position_x': hole.position_x,
                    'position_y': hole.position_y,
                    'target_diameter': hole.target_diameter,
                    'tolerance': hole.tolerance,
                    'status': hole.status
                })
            return result
            
        except Exception as e:
            print(f"获取孔数据失败: {e}")
            return []
        finally:
            self.close_session(session)
    
    def update_hole_status(self, hole_id, new_status, update_source="detection", operator_id=None, batch_id=None):
        """更新孔位状态并记录到状态更新表"""
        session = self.get_session()
        try:
            # 查找孔
            hole = session.query(Hole).filter_by(hole_id=hole_id).first()
            if not hole:
                print(f"未找到孔 {hole_id}")
                return False
            
            old_status = hole.status
            
            # 更新孔位状态
            hole.status = new_status
            hole.updated_at = datetime.now()
            
            # 记录状态更新历史
            status_update = HoleStatusUpdate(
                hole_id=hole.id,
                old_status=old_status,
                new_status=new_status,
                update_source=update_source,
                operator_id=operator_id,
                batch_id=batch_id
            )
            
            session.add(status_update)
            session.commit()
            
            print(f"✅ 孔位 {hole_id} 状态更新: {old_status} -> {new_status}")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ 更新孔位状态失败: {e}")
            return False
        finally:
            self.close_session(session)
    
    def get_pending_status_updates(self, limit=100):
        """获取待同步到全景图的状态更新"""
        session = self.get_session()
        try:
            updates = session.query(HoleStatusUpdate).filter_by(
                sync_to_panorama=False
            ).order_by(HoleStatusUpdate.update_timestamp).limit(limit).all()
            
            result = []
            for update in updates:
                result.append({
                    'id': update.id,
                    'hole_id': update.hole.hole_id,  # 获取hole_id字符串
                    'workpiece_id': update.hole.workpiece_id,
                    'new_status': update.new_status,
                    'update_timestamp': update.update_timestamp,
                    'update_source': update.update_source,
                    'batch_id': update.batch_id
                })
            return result
            
        except Exception as e:
            print(f"❌ 获取待更新状态失败: {e}")
            return []
        finally:
            self.close_session(session)
    
    def mark_status_updates_synced(self, update_ids):
        """标记状态更新为已同步"""
        session = self.get_session()
        try:
            session.query(HoleStatusUpdate).filter(
                HoleStatusUpdate.id.in_(update_ids)
            ).update({
                'sync_to_panorama': True,
                'sync_timestamp': datetime.now()
            }, synchronize_session=False)
            
            session.commit()
            print(f"✅ 标记 {len(update_ids)} 个状态更新为已同步")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ 标记同步状态失败: {e}")
            return False
        finally:
            self.close_session(session)
    
    def get_status_update_stats(self):
        """获取状态更新统计信息"""
        session = self.get_session()
        try:
            total_updates = session.query(HoleStatusUpdate).count()
            pending_updates = session.query(HoleStatusUpdate).filter_by(sync_to_panorama=False).count()
            synced_updates = total_updates - pending_updates
            
            return {
                'total_updates': total_updates,
                'pending_updates': pending_updates,
                'synced_updates': synced_updates,
                'sync_rate': (synced_updates / total_updates * 100) if total_updates > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}
        finally:
            self.close_session(session)


# 全局数据库管理器实例
db_manager = DatabaseManager()


if __name__ == "__main__":
    # 测试数据库功能
    print("初始化数据库...")
    db_manager.create_sample_data()
    
    # 添加一些测试数据
    print("添加测试数据...")
    import numpy as np
    
    # 为H001添加测量数据
    for i in range(50):
        depth = i * 2.0  # 每2mm一个点
        diameter = 25.0 + 0.1 * np.sin(depth * 0.1) + np.random.normal(0, 0.02)
        db_manager.add_measurement_data("H001", depth, diameter)
        
    # 查询数据
    measurements = db_manager.get_hole_measurements("H001")
    print(f"H001的测量数据: {len(measurements)}条")
    
    holes = db_manager.get_workpiece_holes("WP-2024-001")
    print(f"工件孔数: {len(holes)}个")
