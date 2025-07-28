"""
CSV文件处理组件
负责CSV文件的读取、监控和归档
"""
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import pandas as pd
from PySide6.QtCore import QObject, QTimer, Signal, QFileSystemWatcher
from datetime import datetime
import threading
from ..utils.constants import (
    CSV_CHECK_INTERVAL, CSV_STABLE_THRESHOLD, CSV_ARCHIVE_FOLDER,
    DATA_FOLDER
)


class CSVProcessor(QObject):
    """CSV文件处理器"""
    
    # 信号定义
    new_data_available = Signal(list, list)  # 深度数据，直径数据
    file_changed = Signal(str)  # 文件路径
    file_archived = Signal(str, str)  # 原路径，归档路径
    error_occurred = Signal(str)  # 错误信息
    
    def __init__(self):
        super().__init__()
        
        # 文件监控器
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.fileChanged.connect(self._on_file_changed)
        
        # 当前监控的文件
        self._current_file = None
        self._last_modified = None
        self._last_size = 0
        
        # 稳定性检查定时器
        self._stability_timer = QTimer()
        self._stability_timer.timeout.connect(self._check_file_stability)
        self._stability_timer.setInterval(1000)  # 1秒检查一次
        
        # CSV更新检查定时器
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._check_csv_update)
        self._update_timer.setInterval(CSV_CHECK_INTERVAL)
        
        # 数据缓存
        self._cached_data = None
        self._cache_file_path = None
        self._cache_modified_time = None
        
        # 线程锁
        self._lock = threading.Lock()
        
        # 归档目录
        self._archive_dir = Path(DATA_FOLDER) / CSV_ARCHIVE_FOLDER
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        
    def set_csv_file(self, file_path: str):
        """设置要监控的CSV文件"""
        with self._lock:
            # 停止监控旧文件
            if self._current_file and self._current_file in self._file_watcher.files():
                self._file_watcher.removePath(self._current_file)
                
            # 设置新文件
            self._current_file = file_path
            
            if os.path.exists(file_path):
                # 添加文件监控
                self._file_watcher.addPath(file_path)
                
                # 记录文件信息
                self._last_modified = os.path.getmtime(file_path)
                self._last_size = os.path.getsize(file_path)
                
                # 立即读取数据
                self._read_csv_data()
                
                # 启动定时器
                self._update_timer.start()
            else:
                self.error_occurred.emit(f"CSV文件不存在: {file_path}")
                
    def start_monitoring(self):
        """开始监控"""
        if self._current_file:
            self._update_timer.start()
            
    def stop_monitoring(self):
        """停止监控"""
        self._update_timer.stop()
        self._stability_timer.stop()
        
    def get_current_file(self) -> Optional[str]:
        """获取当前监控的文件路径"""
        with self._lock:
            return self._current_file
            
    def read_csv_data(self, file_path: Optional[str] = None) -> Tuple[List[float], List[float]]:
        """读取CSV数据"""
        if file_path is None:
            file_path = self._current_file
            
        if not file_path or not os.path.exists(file_path):
            return [], []
            
        try:
            # 检查缓存
            if (self._cache_file_path == file_path and 
                self._cached_data is not None and
                self._cache_modified_time == os.path.getmtime(file_path)):
                return self._cached_data
                
            # 读取CSV文件
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 提取深度和直径数据
            depth_data = []
            diameter_data = []
            
            # 尝试不同的列名组合
            depth_columns = ['深度', 'Depth', 'depth', '探头深度', 'ProbeDepth']
            diameter_columns = ['直径', 'Diameter', 'diameter', '管孔直径', 'HoleDiameter']
            
            depth_col = None
            diameter_col = None
            
            # 查找深度列
            for col in depth_columns:
                if col in df.columns:
                    depth_col = col
                    break
                    
            # 查找直径列
            for col in diameter_columns:
                if col in df.columns:
                    diameter_col = col
                    break
                    
            if depth_col and diameter_col:
                depth_data = df[depth_col].astype(float).tolist()
                diameter_data = df[diameter_col].astype(float).tolist()
                
                # 更新缓存
                self._cached_data = (depth_data, diameter_data)
                self._cache_file_path = file_path
                self._cache_modified_time = os.path.getmtime(file_path)
            else:
                available_cols = ', '.join(df.columns.tolist())
                self.error_occurred.emit(f"CSV文件缺少必需的列。可用列: {available_cols}")
                
            return depth_data, diameter_data
            
        except Exception as e:
            self.error_occurred.emit(f"读取CSV文件失败: {str(e)}")
            return [], []
            
    def archive_current_file(self) -> Optional[str]:
        """归档当前文件"""
        with self._lock:
            if not self._current_file or not os.path.exists(self._current_file):
                return None
                
            try:
                # 生成归档文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_name = Path(self._current_file).stem
                archive_name = f"{original_name}_{timestamp}.csv"
                archive_path = self._archive_dir / archive_name
                
                # 复制文件到归档目录
                shutil.copy2(self._current_file, archive_path)
                
                # 发送归档信号
                self.file_archived.emit(self._current_file, str(archive_path))
                
                return str(archive_path)
                
            except Exception as e:
                self.error_occurred.emit(f"归档文件失败: {str(e)}")
                return None
                
    def get_archive_list(self) -> List[Dict[str, any]]:
        """获取归档文件列表"""
        archive_files = []
        
        try:
            for file_path in self._archive_dir.glob("*.csv"):
                stat = file_path.stat()
                archive_files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'created': datetime.fromtimestamp(stat.st_ctime)
                })
                
            # 按修改时间排序（最新的在前）
            archive_files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            self.error_occurred.emit(f"获取归档列表失败: {str(e)}")
            
        return archive_files
        
    def clean_old_archives(self, days: int = 30):
        """清理旧的归档文件"""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for file_path in self._archive_dir.glob("*.csv"):
                if file_path.stat().st_mtime < cutoff_date:
                    file_path.unlink()
                    
        except Exception as e:
            self.error_occurred.emit(f"清理归档文件失败: {str(e)}")
            
    def _on_file_changed(self, path: str):
        """文件变化回调"""
        # 启动稳定性检查
        self._stability_timer.start()
        self.file_changed.emit(path)
        
    def _check_file_stability(self):
        """检查文件稳定性"""
        if not self._current_file or not os.path.exists(self._current_file):
            self._stability_timer.stop()
            return
            
        current_size = os.path.getsize(self._current_file)
        current_modified = os.path.getmtime(self._current_file)
        
        # 检查文件是否稳定（大小和修改时间不再变化）
        if (current_size == self._last_size and 
            current_modified == self._last_modified):
            # 文件稳定，读取数据
            self._stability_timer.stop()
            self._read_csv_data()
        else:
            # 更新记录
            self._last_size = current_size
            self._last_modified = current_modified
            
    def _check_csv_update(self):
        """定期检查CSV更新"""
        if not self._current_file or not os.path.exists(self._current_file):
            return
            
        # 检查文件是否有更新
        current_modified = os.path.getmtime(self._current_file)
        if current_modified != self._last_modified:
            self._last_modified = current_modified
            self._read_csv_data()
            
    def _read_csv_data(self):
        """内部读取CSV数据并发送信号"""
        depth_data, diameter_data = self.read_csv_data()
        if depth_data and diameter_data:
            self.new_data_available.emit(depth_data, diameter_data)
            
    def export_data_to_csv(self, depth_data: List[float], diameter_data: List[float], 
                          file_path: str, additional_columns: Optional[Dict[str, List]] = None):
        """导出数据到CSV文件"""
        try:
            # 创建数据字典
            data = {
                '深度': depth_data,
                '直径': diameter_data
            }
            
            # 添加额外的列
            if additional_columns:
                data.update(additional_columns)
                
            # 创建DataFrame并保存
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"导出CSV失败: {str(e)}")
            return False
            
    def get_csv_info(self, file_path: Optional[str] = None) -> Optional[Dict[str, any]]:
        """获取CSV文件信息"""
        if file_path is None:
            file_path = self._current_file
            
        if not file_path or not os.path.exists(file_path):
            return None
            
        try:
            stat = os.stat(file_path)
            df = pd.read_csv(file_path, encoding='utf-8')
            
            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'rows': len(df),
                'columns': list(df.columns),
                'memory_usage': df.memory_usage(deep=True).sum()
            }
            
        except Exception as e:
            self.error_occurred.emit(f"获取CSV信息失败: {str(e)}")
            return None