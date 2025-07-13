"""内窥镜图像管理器模块"""
import os
import re
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import QObject, Signal, QTimer


class EndoscopeManager(QObject):
    """
    内窥镜图像管理器
    负责图像加载、切换和显示控制
    """
    
    # 信号定义
    images_loaded = Signal(int)  # 图像数量
    image_changed = Signal(int)  # 新图像索引
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 图像列表
        self.current_images: List[str] = []
        self.current_image_index = 0
        self.image_switch_points: List[int] = []
        
        # 自动切换控制
        self.switching_enabled = False
        self.switch_timer = QTimer()
        self.switch_timer.timeout.connect(self._switch_to_next_image)
        self.switch_interval = 5000  # 5秒
        
        # 图像路径映射
        self.hole_image_mapping = self._init_hole_image_mapping()
        
    def _init_hole_image_mapping(self) -> dict:
        """初始化孔位到图像路径的映射"""
        return {
            'H00001': 'Data/H00001/BISDM/result',
            'H00002': 'Data/H00002/BISDM/result'
        }
        
    def load_images_for_hole(self, hole_id: str) -> bool:
        """加载指定孔位的图像"""
        if hole_id not in self.hole_image_mapping:
            self.error_occurred.emit(f"孔位 {hole_id} 没有对应的图像路径")
            return False
            
        image_dir = self.hole_image_mapping[hole_id]
        return self.load_images_from_directory(image_dir)
        
    def load_images_from_directory(self, directory: str) -> bool:
        """从目录加载图像"""
        try:
            self.current_images.clear()
            self.current_image_index = 0
            
            if not os.path.exists(directory):
                self.error_occurred.emit(f"图像目录不存在: {directory}")
                return False
                
            # 获取所有PNG文件
            image_files = []
            for file in os.listdir(directory):
                if file.lower().endswith('.png'):
                    image_files.append(os.path.join(directory, file))
                    
            if not image_files:
                self.error_occurred.emit(f"目录 {directory} 中没有找到PNG图像")
                return False
                
            # 按文件名中的数字排序
            self.current_images = sorted(image_files, key=self._extract_number)
            
            # 计算图像切换点
            self._calculate_switch_points()
            
            self.images_loaded.emit(len(self.current_images))
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"加载图像失败: {str(e)}")
            return False
            
    def _extract_number(self, filename: str) -> float:
        """从文件名中提取数字用于排序"""
        base_name = os.path.basename(filename)
        # 匹配形如 "2-7.0.png" 的文件名
        match = re.search(r'(\d+)-(\d+(?:\.\d+)?)', base_name)
        if match:
            first_num = int(match.group(1))
            second_num = float(match.group(2))
            return first_num * 1000 + second_num
        return 0
        
    def _calculate_switch_points(self):
        """计算图像切换点"""
        if len(self.current_images) <= 1:
            self.image_switch_points = []
            return
            
        # 均匀分布切换点
        total_points = 1000  # 假设总共1000个数据点
        images_count = len(self.current_images)
        interval = total_points // images_count
        
        self.image_switch_points = [i * interval for i in range(images_count)]
        
    def start_auto_switching(self, interval: int = 5000):
        """开始自动切换图像"""
        if not self.current_images:
            return
            
        self.switch_interval = interval
        self.switching_enabled = True
        self.switch_timer.start(interval)
        
    def stop_auto_switching(self):
        """停止自动切换"""
        self.switching_enabled = False
        self.switch_timer.stop()
        
    def _switch_to_next_image(self):
        """切换到下一张图像"""
        if not self.current_images:
            return
            
        self.current_image_index = (self.current_image_index + 1) % len(self.current_images)
        self.image_changed.emit(self.current_image_index)
        
    def set_image_by_index(self, index: int):
        """设置当前图像索引"""
        if 0 <= index < len(self.current_images):
            self.current_image_index = index
            self.image_changed.emit(index)
            
    def set_image_by_progress(self, progress: float):
        """根据进度设置图像（0.0-1.0）"""
        if not self.current_images:
            return
            
        index = int(progress * (len(self.current_images) - 1))
        self.set_image_by_index(index)
        
    def get_current_image_path(self) -> Optional[str]:
        """获取当前图像路径"""
        if 0 <= self.current_image_index < len(self.current_images):
            return self.current_images[self.current_image_index]
        return None
        
    def get_image_count(self) -> int:
        """获取图像数量"""
        return len(self.current_images)
        
    def reset(self):
        """重置管理器"""
        self.stop_auto_switching()
        self.current_images.clear()
        self.current_image_index = 0
        self.image_switch_points.clear()