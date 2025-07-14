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
                workpiece_id="CAP1000",
                name="管板工件",
                type="tube_plate",
                material="母材材质：SA508.Gr3. C1.2；堆焊层材质：镍基堆焊层 "
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

    def get_workpiece_list(self):
        """获取工件列表"""
        session = self.get_session()
        try:
            workpieces = session.query(Workpiece).all()
            return [w.workpiece_id for w in workpieces]
        except Exception as e:
            print(f"获取工件列表失败: {e}")
            return []
        finally:
            self.close_session(session)

    def get_hole_list(self, workpiece_id):
        """获取指定工件的孔位列表"""
        session = self.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=workpiece_id).first()
            if not workpiece:
                return []

            holes = session.query(Hole).filter_by(workpiece_id=workpiece.id).all()
            return [h.hole_id for h in holes]
        except Exception as e:
            print(f"获取孔位列表失败: {e}")
            return []
        finally:
            self.close_session(session)

    def get_measurement_data(self, workpiece_id, hole_id):
        """获取测量数据 - 兼容历史查看器接口"""
        session = self.get_session()
        try:
            # 查找孔
            workpiece = session.query(Workpiece).filter_by(workpiece_id=workpiece_id).first()
            if not workpiece:
                return []

            hole = session.query(Hole).filter(
                Hole.hole_id == hole_id,
                Hole.workpiece_id == workpiece.id
            ).first()
            if not hole:
                return []

            measurements = session.query(Measurement).filter_by(hole_id=hole.id).order_by(Measurement.depth).all()

            # 转换为历史查看器期望的格式
            result = []
            for m in measurements:
                # 生成模拟的通道数据
                import random
                channel1 = random.uniform(1300, 1600)
                channel2 = random.uniform(1300, 1600)
                channel3 = random.uniform(1300, 1600)

                result.append({
                    'position': m.depth,
                    'diameter': m.diameter,
                    'channel1': channel1,
                    'channel2': channel2,
                    'channel3': channel3,
                    'qualified': m.is_qualified,
                    'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M:%S') if m.timestamp else '',
                    'operator': m.operator
                })
            return result

        except Exception as e:
            print(f"获取测量数据失败: {e}")
            return []
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
    
    holes = db_manager.get_workpiece_holes("CAP1000")
    print(f"工件孔数: {len(holes)}个")
