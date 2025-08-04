"""
内窥镜管理组件
负责内窥镜图像的采集、切换和显示
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QPixmap
from collections import deque
from datetime import datetime
import shutil
from ..utils.constants import (
    ENDOSCOPE_SWITCH_INTERVAL, ENDOSCOPE_IMAGE_CACHE_SIZE,
    ROWS, COLUMNS
)


class EndoscopeManager(QObject):
    """内窥镜管理器"""
    
    # 信号定义
    image_updated = Signal(str, QPixmap)  # 孔位ID，图像
    probe_switched = Signal(int)  # 探头编号
    position_changed = Signal(str)  # 孔位ID
    error_occurred = Signal(str)  # 错误信息
    
    def __init__(self):
        super().__init__()
        
        # 探头设置
        self._current_probe = 1  # 当前探头编号
        self._probe_count = 2    # 探头总数
        
        # 孔位信息
        self._current_position = None  # 当前孔位
        self._position_mapping = {}    # 孔位到文件路径的映射
        
        # 获取当前产品相关的图像目录
        from src.core.shared_data_manager import SharedDataManager
        from src.models.data_path_manager import DataPathManager
        
        self._shared_data = SharedDataManager()
        self._path_manager = DataPathManager()
        
        # 延迟初始化图像目录，等待产品选择
        self._image_base_dir = None
        self._probe1_dir = None
        self._probe2_dir = None
        self._initialized = False
        
        # 监听产品变更
        self._shared_data.data_changed.connect(self._on_product_changed)
        
        # 图像缓存
        self._image_cache = {}  # {孔位ID: {探头1: QPixmap, 探头2: QPixmap}}
        self._cache_queue = deque(maxlen=ENDOSCOPE_IMAGE_CACHE_SIZE)
        
        # 自动切换定时器
        self._switch_timer = QTimer()
        self._switch_timer.timeout.connect(self._auto_switch_probe)
        self._switch_interval = ENDOSCOPE_SWITCH_INTERVAL
        
        # 初始化孔位映射
        self._init_position_mapping()
        
        # 尝试初始化当前产品的目录
        self._try_initialize_directories()
        
    def _init_position_mapping(self):
        """初始化孔位映射"""
        for row in ROWS:
            for col in COLUMNS:
                position_id = f"{row}{col}"
                self._position_mapping[position_id] = {
                    'row': row,
                    'column': col,
                    'index': (ROWS.index(row) * len(COLUMNS)) + (col - 1)
                }
                
    def set_current_position(self, position_id: str):
        """设置当前孔位"""
        if position_id in self._position_mapping:
            self._current_position = position_id
            self.position_changed.emit(position_id)
            
            # 更新显示的图像
            self._update_current_image()
        else:
            self.error_occurred.emit(f"无效的孔位ID: {position_id}")
            
    def set_current_probe(self, probe_number: int):
        """设置当前探头"""
        if 1 <= probe_number <= self._probe_count:
            self._current_probe = probe_number
            self.probe_switched.emit(probe_number)
            
            # 更新显示的图像
            self._update_current_image()
        else:
            self.error_occurred.emit(f"无效的探头编号: {probe_number}")
            
    def start_auto_switch(self, interval: Optional[int] = None):
        """启动自动切换"""
        if interval:
            self._switch_interval = interval
            self._switch_timer.setInterval(interval)
            
        self._switch_timer.start()
        
    def stop_auto_switch(self):
        """停止自动切换"""
        self._switch_timer.stop()
        
    def get_image_for_position(self, position_id: str, probe_number: Optional[int] = None) -> Optional[QPixmap]:
        """获取指定孔位的图像"""
        if probe_number is None:
            probe_number = self._current_probe
            
        # 检查缓存
        cache_key = f"{position_id}_probe{probe_number}"
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]
            
        # 构建图像路径
        image_path = self._get_image_path(position_id, probe_number)
        
        if image_path and os.path.exists(image_path):
            try:
                pixmap = QPixmap(str(image_path))
                if not pixmap.isNull():
                    # 添加到缓存
                    self._add_to_cache(cache_key, pixmap)
                    return pixmap
            except Exception as e:
                self.error_occurred.emit(f"加载图像失败: {str(e)}")
                
        return None
        
    def save_current_image(self, image_data: bytes, probe_number: Optional[int] = None):
        """保存当前位置的图像"""
        if not self._current_position:
            self.error_occurred.emit("未设置当前孔位")
            return False
            
        if probe_number is None:
            probe_number = self._current_probe
            
        # 构建保存路径
        probe_dir = self._probe1_dir if probe_number == 1 else self._probe2_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self._current_position}_{timestamp}.jpg"
        file_path = probe_dir / filename
        
        try:
            # 保存图像
            with open(file_path, 'wb') as f:
                f.write(image_data)
                
            # 更新缓存
            pixmap = QPixmap(str(file_path))
            if not pixmap.isNull():
                cache_key = f"{self._current_position}_probe{probe_number}"
                self._add_to_cache(cache_key, pixmap)
                
                # 发送更新信号
                self.image_updated.emit(self._current_position, pixmap)
                
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"保存图像失败: {str(e)}")
            return False
            
    def get_available_positions(self) -> List[str]:
        """获取所有有图像的孔位"""
        positions = set()
        
        # 扫描两个探头目录
        for probe_dir in [self._probe1_dir, self._probe2_dir]:
            if probe_dir.exists():
                for file_path in probe_dir.glob("*.jpg"):
                    # 从文件名提取孔位ID
                    filename = file_path.stem
                    if '_' in filename:
                        position_id = filename.split('_')[0]
                        if position_id in self._position_mapping:
                            positions.add(position_id)
                            
        return sorted(list(positions))
        
    def get_probe_status(self) -> Dict[str, any]:
        """获取探头状态"""
        return {
            'current_probe': self._current_probe,
            'total_probes': self._probe_count,
            'auto_switch_enabled': self._switch_timer.isActive(),
            'switch_interval': self._switch_interval,
            'current_position': self._current_position
        }
        
    def clear_position_images(self, position_id: str):
        """清除指定孔位的所有图像"""
        cleared_count = 0
        
        for probe_dir in [self._probe1_dir, self._probe2_dir]:
            if probe_dir.exists():
                for file_path in probe_dir.glob(f"{position_id}_*.jpg"):
                    try:
                        file_path.unlink()
                        cleared_count += 1
                    except Exception as e:
                        self.error_occurred.emit(f"删除图像失败: {str(e)}")
                        
        # 清除缓存
        cache_keys_to_remove = [key for key in self._image_cache.keys() 
                               if key.startswith(position_id)]
        for key in cache_keys_to_remove:
            del self._image_cache[key]
            
        return cleared_count
        
    def export_images(self, export_dir: str, positions: Optional[List[str]] = None) -> int:
        """导出图像到指定目录"""
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        exported_count = 0
        
        if positions is None:
            positions = self.get_available_positions()
            
        for position_id in positions:
            # 创建孔位子目录
            position_dir = export_path / position_id
            position_dir.mkdir(exist_ok=True)
            
            # 复制两个探头的图像
            for probe_num in range(1, self._probe_count + 1):
                probe_dir = self._probe1_dir if probe_num == 1 else self._probe2_dir
                
                for file_path in probe_dir.glob(f"{position_id}_*.jpg"):
                    try:
                        dest_path = position_dir / f"probe{probe_num}_{file_path.name}"
                        shutil.copy2(file_path, dest_path)
                        exported_count += 1
                    except Exception as e:
                        self.error_occurred.emit(f"导出图像失败: {str(e)}")
                        
        return exported_count
        
    def _auto_switch_probe(self):
        """自动切换探头"""
        # 切换到另一个探头
        new_probe = 2 if self._current_probe == 1 else 1
        self.set_current_probe(new_probe)
        
    def _update_current_image(self):
        """更新当前显示的图像"""
        if self._current_position:
            pixmap = self.get_image_for_position(self._current_position)
            if pixmap:
                self.image_updated.emit(self._current_position, pixmap)
                
    def _on_product_changed(self, key: str, value):
        """产品变更时的处理"""
        if key == 'current_product':
            self._try_initialize_directories()
    
    def _try_initialize_directories(self):
        """尝试初始化目录"""
        try:
            current_product = self._shared_data.get_data('current_product')
            if current_product and not self._initialized:
                product_name = current_product.get('model_name', 'DefaultProduct')
                
                # 获取产品特定的内窥镜图像目录
                product_path = self._path_manager.get_product_path(product_name)
                self._image_base_dir = Path(product_path) / "内窥镜图片"
                self._probe1_dir = self._image_base_dir / "探头1"
                self._probe2_dir = self._image_base_dir / "探头2"
                
                self._initialized = True
                print(f"✅ EndoscopeManager 已初始化产品 {product_name} 的图像目录")
        except Exception as e:
            print(f"⚠️ EndoscopeManager 初始化失败: {e}")
    
    def _ensure_directories_exist(self):
        """按需创建目录"""
        if not self._initialized:
            self._try_initialize_directories()
        
        if self._probe1_dir and self._probe2_dir:
            self._probe1_dir.mkdir(parents=True, exist_ok=True)
            self._probe2_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_image_path(self, position_id: str, probe_number: int) -> Optional[Path]:
        """获取图像文件路径"""
        self._ensure_directories_exist()
        
        if not self._probe1_dir or not self._probe2_dir:
            return None
            
        probe_dir = self._probe1_dir if probe_number == 1 else self._probe2_dir
        
        # 查找最新的图像文件
        pattern = f"{position_id}_*.jpg"
        files = list(probe_dir.glob(pattern))
        
        if files:
            # 返回最新的文件
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return files[0]
            
        return None
        
    def _add_to_cache(self, cache_key: str, pixmap: QPixmap):
        """添加到缓存"""
        # 如果缓存已满，移除最旧的项
        if len(self._cache_queue) >= ENDOSCOPE_IMAGE_CACHE_SIZE:
            oldest_key = self._cache_queue.popleft()
            if oldest_key in self._image_cache:
                del self._image_cache[oldest_key]
                
        # 添加新项
        self._image_cache[cache_key] = pixmap
        self._cache_queue.append(cache_key)
        
    def get_image_statistics(self) -> Dict[str, any]:
        """获取图像统计信息"""
        total_images = 0
        probe1_images = 0
        probe2_images = 0
        positions_with_images = set()
        
        # 统计探头1的图像
        if self._probe1_dir.exists():
            probe1_files = list(self._probe1_dir.glob("*.jpg"))
            probe1_images = len(probe1_files)
            total_images += probe1_images
            
            for file_path in probe1_files:
                position_id = file_path.stem.split('_')[0]
                positions_with_images.add(position_id)
                
        # 统计探头2的图像
        if self._probe2_dir.exists():
            probe2_files = list(self._probe2_dir.glob("*.jpg"))
            probe2_images = len(probe2_files)
            total_images += probe2_images
            
            for file_path in probe2_files:
                position_id = file_path.stem.split('_')[0]
                positions_with_images.add(position_id)
                
        return {
            'total_images': total_images,
            'probe1_images': probe1_images,
            'probe2_images': probe2_images,
            'positions_with_images': len(positions_with_images),
            'cache_size': len(self._image_cache)
        }