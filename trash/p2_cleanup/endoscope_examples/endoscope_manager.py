"""
P2 内窥镜管理器
负责内窥镜设备的连接、控制和数据管理
"""

from PySide6.QtCore import QObject, Signal, QTimer, Slot
from PySide6.QtGui import QPixmap
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class EndoscopeManager(QObject):
    """
    内窥镜管理器
    
    功能：
    1. 设备连接管理
    2. 图像采集控制
    3. 数据保存和管理
    4. 设备状态监控
    """
    
    # 信号定义
    device_connected = Signal(bool)  # 设备连接状态
    image_acquired = Signal(QPixmap)  # 图像采集信号
    acquisition_started = Signal()  # 采集开始信号
    acquisition_stopped = Signal()  # 采集停止信号
    error_occurred = Signal(str)  # 错误信号
    status_changed = Signal(str)  # 状态改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 设备状态
        self.is_connected = False
        self.is_acquiring = False
        self.device_info = {}
        
        # 采集参数
        self.acquisition_interval = 1000  # ms
        self.save_images = False
        
        # 当前检测信息
        self.current_hole_id = None
        self.current_batch_id = None
        self.current_product_id = None
        
        # 数据路径管理器
        self.path_manager = None
        self.save_directory = None
        
        # 服务引用
        self.business_service = None
        self.shared_data_manager = None
        
        # 图像采集定时器
        self.acquisition_timer = QTimer()
        self.acquisition_timer.timeout.connect(self._acquire_image)
        
        # 设备监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._monitor_device)
        self.monitor_timer.start(2000)  # 2秒检查一次设备状态
        
        # 初始化数据路径管理器
        self._init_path_manager()
        
    def _init_path_manager(self):
        """初始化数据路径管理器和服务引用"""
        try:
            from src.core.data_path_manager import get_data_path_manager
            self.path_manager = get_data_path_manager()
            self.logger.debug("数据路径管理器初始化成功")
            
            # 初始化服务引用
            self._init_services()
            
        except Exception as e:
            self.logger.error(f"初始化数据路径管理器失败: {e}")
    
    def _init_services(self):
        """初始化服务引用"""
        try:
            # 获取业务服务
            from src.shared.services import get_business_service
            self.business_service = get_business_service()
            
            # 获取共享数据管理器
            from src.core.shared_data_manager import SharedDataManager
            self.shared_data_manager = SharedDataManager()
            
            self.logger.debug("服务引用初始化成功")
        except Exception as e:
            self.logger.warning(f"服务引用初始化失败: {e}")
    
    def _get_current_batch_context(self) -> tuple[Optional[str], Optional[str]]:
        """动态获取当前批次上下文信息"""
        try:
            product_id = None
            batch_id = None
            
            # 1. 从业务服务获取当前产品信息
            if self.business_service and hasattr(self.business_service, 'current_product'):
                current_product = self.business_service.current_product
                if current_product:
                    if hasattr(current_product, 'model_name'):
                        product_id = current_product.model_name
                    elif hasattr(current_product, 'workpiece_id'):
                        product_id = current_product.workpiece_id
                    else:
                        product_id = str(current_product)
            
            # 2. 从检测服务获取当前批次ID
            from src.shared.services.detection_service import DetectionService
            detection_service = DetectionService()
            if hasattr(detection_service, 'current_batch_id') and detection_service.current_batch_id:
                batch_id = detection_service.current_batch_id
            
            # 3. 如果没有找到，尝试从其他地方获取
            if not batch_id:
                # 可以从全局状态、配置文件或其他服务获取
                pass
            
            self.logger.debug(f"当前批次上下文: product_id={product_id}, batch_id={batch_id}")
            return product_id, batch_id
            
        except Exception as e:
            self.logger.warning(f"获取当前批次上下文失败: {e}")
            return None, None
    
    def _update_save_directory(self):
        """根据当前批次信息更新保存目录"""
        try:
            if not self.path_manager:
                self.save_directory = None
                return
            
            # 动态获取当前批次上下文（如果没有手动设置）
            if not self.current_product_id or not self.current_batch_id:
                product_id, batch_id = self._get_current_batch_context()
                if product_id and batch_id:
                    self.current_product_id = product_id
                    self.current_batch_id = batch_id
                    self.logger.info(f"自动获取批次上下文: {product_id}/{batch_id}")
                else:
                    self.logger.warning("无法获取当前批次上下文，跳过目录更新")
                    self.save_directory = None
                    return
            
            # 使用标准的BISDM目录结构保存内窥镜图像
            if self.current_hole_id:
                # 保存到特定孔位的BISDM目录
                bisdm_dir = self.path_manager.get_hole_bisdm_dir(
                    self.current_product_id, 
                    self.current_batch_id, 
                    self.current_hole_id
                )
                self.save_directory = Path(bisdm_dir) / "endoscope_images"
            else:
                # 保存到批次根目录的内窥镜图像目录
                batch_dir = self.path_manager.get_inspection_batch_path(
                    self.current_product_id, 
                    self.current_batch_id
                )
                self.save_directory = Path(batch_dir) / "endoscope_images"
            
            # 确保目录存在
            if self.save_directory:
                self.save_directory.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"内窥镜图像保存目录更新为: {self.save_directory}")
                
        except Exception as e:
            self.logger.error(f"更新保存目录失败: {e}")
            self.save_directory = None
    
    def connect_device(self, device_config: Optional[Dict[str, Any]] = None):
        """
        连接内窥镜设备
        
        Args:
            device_config: 设备配置参数
        """
        try:
            self.logger.info("正在连接内窥镜设备...")
            
            # TODO: 实现实际的设备连接逻辑
            # 这里是模拟连接
            self.is_connected = True
            self.device_info = {
                "model": "Simulated Endoscope",
                "serial": "SIM001",
                "resolution": "1920x1080",
                "fps": 30
            }
            
            self.device_connected.emit(True)
            self.status_changed.emit("设备已连接")
            self.logger.info("内窥镜设备连接成功")
            
        except Exception as e:
            self.logger.error(f"连接内窥镜设备失败: {e}")
            self.error_occurred.emit(f"设备连接失败: {str(e)}")
            self.is_connected = False
            self.device_connected.emit(False)
    
    def disconnect_device(self):
        """断开设备连接"""
        try:
            if self.is_acquiring:
                self.stop_acquisition()
                
            # TODO: 实现实际的设备断开逻辑
            self.is_connected = False
            self.device_info.clear()
            
            self.device_connected.emit(False)
            self.status_changed.emit("设备已断开")
            self.logger.info("内窥镜设备已断开")
            
        except Exception as e:
            self.logger.error(f"断开设备失败: {e}")
            self.error_occurred.emit(f"设备断开失败: {str(e)}")
    
    def start_acquisition(self):
        """开始图像采集"""
        try:
            if not self.is_connected:
                raise RuntimeError("设备未连接")
                
            if self.is_acquiring:
                self.logger.warning("图像采集已在进行中")
                return
                
            self.is_acquiring = True
            self.acquisition_timer.start(self.acquisition_interval)
            
            self.acquisition_started.emit()
            self.status_changed.emit("正在采集图像")
            self.logger.info("开始内窥镜图像采集")
            
        except Exception as e:
            self.logger.error(f"开始图像采集失败: {e}")
            self.error_occurred.emit(f"采集启动失败: {str(e)}")
    
    def stop_acquisition(self):
        """停止图像采集"""
        try:
            if not self.is_acquiring:
                self.logger.warning("图像采集未在进行")
                return
                
            self.is_acquiring = False
            self.acquisition_timer.stop()
            
            self.acquisition_stopped.emit()
            self.status_changed.emit("采集已停止")
            self.logger.info("停止内窥镜图像采集")
            
        except Exception as e:
            self.logger.error(f"停止图像采集失败: {e}")
            self.error_occurred.emit(f"采集停止失败: {str(e)}")
    
    @Slot()
    def _acquire_image(self):
        """采集图像"""
        try:
            if not self.is_connected or not self.is_acquiring:
                return
                
            # TODO: 从实际设备获取图像
            # 目前生成模拟图像
            pixmap = self._generate_simulated_image()
            
            if pixmap and not pixmap.isNull():
                # 保存图像（如果启用）
                if self.save_images:
                    self._save_image(pixmap)
                
                # 发射图像信号
                self.image_acquired.emit(pixmap)
                
        except Exception as e:
            self.logger.error(f"图像采集失败: {e}")
            self.error_occurred.emit(f"图像采集失败: {str(e)}")
    
    def _generate_simulated_image(self) -> QPixmap:
        """生成模拟内窥镜图像"""
        try:
            from PySide6.QtGui import QPainter, QColor, QBrush, QPen
            from PySide6.QtCore import QRect
            import random
            
            # 创建基础图像
            pixmap = QPixmap(640, 480)
            pixmap.fill(QColor(20, 20, 30))  # 深色背景
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 绘制圆形视野
            center_x, center_y = 320, 240
            radius = 200
            
            # 外圈
            painter.setBrush(QBrush(QColor(40, 40, 60)))
            painter.setPen(QPen(QColor(80, 80, 120), 2))
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
            
            # 内部细节
            painter.setBrush(QBrush(QColor(60, 40, 40)))
            for _ in range(5):
                x = center_x + random.randint(-radius//2, radius//2)
                y = center_y + random.randint(-radius//2, radius//2)
                size = random.randint(10, 30)
                painter.drawEllipse(x - size//2, y - size//2, size, size)
            
            # 模拟表面纹理
            painter.setPen(QPen(QColor(100, 80, 60), 1))
            for _ in range(20):
                x1 = center_x + random.randint(-radius, radius)
                y1 = center_y + random.randint(-radius, radius)
                x2 = x1 + random.randint(-20, 20)
                y2 = y1 + random.randint(-20, 20)
                painter.drawLine(x1, y1, x2, y2)
            
            # 添加信息文本
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(10, 20, f"Hole: {self.current_hole_id or 'N/A'}")
            painter.drawText(10, 40, f"Time: {datetime.now().strftime('%H:%M:%S')}")
            
            painter.end()
            return pixmap
            
        except Exception as e:
            self.logger.error(f"生成模拟图像失败: {e}")
            return QPixmap()
    
    def _save_image(self, pixmap: QPixmap):
        """保存图像到文件"""
        try:
            if not self.save_directory:
                self.logger.warning("保存目录未设置，跳过图像保存")
                return
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"endoscope_{timestamp}"
            
            if self.current_hole_id:
                filename += f"_{self.current_hole_id}"
            if self.current_batch_id:
                filename += f"_{self.current_batch_id}"
                
            filename += ".png"
            filepath = self.save_directory / filename
            
            if pixmap.save(str(filepath)):
                self.logger.debug(f"图像已保存: {filepath}")
                
                # 记录到数据库（如果可用）
                self._record_image_to_database(str(filepath))
            else:
                self.logger.warning(f"图像保存失败: {filepath}")
                
        except Exception as e:
            self.logger.error(f"保存图像失败: {e}")
    
    def _record_image_to_database(self, image_path: str):
        """将图像记录到数据库"""
        try:
            if not self.current_hole_id:
                return
                
            # 尝试记录到数据库
            from src.modules.models import db_manager
            # 这里可以扩展数据库记录功能
            self.logger.debug(f"图像路径已记录: {image_path}")
            
        except Exception as e:
            self.logger.debug(f"记录图像到数据库失败: {e}")
    
    @Slot()
    def _monitor_device(self):
        """监控设备状态"""
        try:
            # TODO: 实现实际的设备状态检查
            # 目前是模拟检查
            if self.is_connected:
                # 模拟偶尔的连接问题
                import random
                if random.random() < 0.001:  # 0.1% 概率模拟连接问题
                    self.logger.warning("检测到设备连接问题")
                    self.error_occurred.emit("设备连接不稳定")
                    
        except Exception as e:
            self.logger.error(f"设备监控失败: {e}")
    
    # 属性设置方法
    def set_acquisition_interval(self, interval_ms: int):
        """设置采集间隔"""
        self.acquisition_interval = max(100, interval_ms)  # 最小100ms
        if self.is_acquiring:
            self.acquisition_timer.stop()
            self.acquisition_timer.start(self.acquisition_interval)
        self.logger.debug(f"采集间隔设置为: {self.acquisition_interval}ms")
    
    def set_save_images(self, enable: bool):
        """设置是否保存图像"""
        self.save_images = enable
        self.logger.debug(f"图像保存: {'启用' if enable else '禁用'}")
    
    def set_save_directory(self, directory: Path):
        """设置保存目录（已废弃，使用set_batch_context代替）"""
        self.logger.warning("set_save_directory已废弃，请使用set_batch_context设置批次上下文")
    
    def set_batch_context(self, product_id: str, batch_id: str):
        """手动设置批次上下文信息"""
        try:
            self.current_product_id = product_id
            self.current_batch_id = batch_id
            self._update_save_directory()
            self.logger.debug(f"批次上下文已手动设置: {product_id}/{batch_id}")
        except Exception as e:
            self.logger.error(f"设置批次上下文失败: {e}")
    
    def refresh_batch_context(self):
        """刷新批次上下文信息（自动获取当前状态）"""
        try:
            product_id, batch_id = self._get_current_batch_context()
            if product_id and batch_id:
                self.current_product_id = product_id
                self.current_batch_id = batch_id
                self._update_save_directory()
                self.logger.info(f"批次上下文已刷新: {product_id}/{batch_id}")
                return True
            else:
                self.logger.warning("无法获取当前批次上下文")
                return False
        except Exception as e:
            self.logger.error(f"刷新批次上下文失败: {e}")
            return False
    
    def set_current_hole(self, hole_id: str, batch_id: Optional[str] = None):
        """设置当前检测的孔位"""
        self.current_hole_id = hole_id
        if batch_id:
            self.current_batch_id = batch_id
        
        # 更新保存目录以反映当前孔位
        self._update_save_directory()
        self.logger.debug(f"设置当前孔位: {hole_id}, 批次: {self.current_batch_id}")
    
    # 状态查询方法
    def is_device_connected(self) -> bool:
        """检查设备是否连接"""
        return self.is_connected
    
    def is_acquisition_running(self) -> bool:
        """检查是否正在采集"""
        return self.is_acquiring
    
    def get_device_info(self) -> Dict[str, Any]:
        """获取设备信息"""
        return self.device_info.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "connected": self.is_connected,
            "acquiring": self.is_acquiring,
            "interval": self.acquisition_interval,
            "save_images": self.save_images,
            "save_directory": str(self.save_directory) if self.save_directory else None,
            "product_id": self.current_product_id,
            "batch_id": self.current_batch_id,
            "current_hole": self.current_hole_id,
            "current_batch": self.current_batch_id,
            "device_info": self.device_info
        }