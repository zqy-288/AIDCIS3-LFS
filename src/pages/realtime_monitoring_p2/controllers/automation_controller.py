"""
自动化控制器
管理自动化任务和文件监控
"""

from PySide6.QtCore import QObject, Signal, QFileSystemWatcher, QTimer
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import os


class AutomationController(QObject):
    """
    自动化控制器
    
    负责：
    1. 文件监控
    2. 自动数据导入
    3. 批量处理
    4. 定时任务
    """
    
    # 信号定义
    file_detected = Signal(str)  # 检测到新文件
    automation_started = Signal()  # 自动化启动
    automation_stopped = Signal()  # 自动化停止
    task_completed = Signal(str)  # 任务完成
    error_occurred = Signal(str)  # 发生错误
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 文件监控器
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.directoryChanged.connect(self._on_directory_changed)
        
        # 获取当前产品相关的监控目录
        from src.core.shared_data_manager import SharedDataManager
        from src.models.data_path_manager import DataPathManager
        
        self._shared_data = SharedDataManager()
        self._path_manager = DataPathManager()
        
        # 延迟初始化监控目录，等待产品选择
        self.watch_directory = None
        self._initialized = False
        self.file_extensions = ['.csv', '.txt', '.dat']
        
        # 监听产品变更
        self._shared_data.data_changed.connect(self._on_product_changed)
        
        # 尝试初始化当前产品的目录
        self._try_initialize_directory()
        
        # 自动化状态
        self.is_automation_enabled = False
        self.processed_files = set()
        
        # 定时器用于批处理
        self.batch_timer = QTimer()
        self.batch_timer.timeout.connect(self._process_batch)
        self.pending_files = []
        
    def _on_product_changed(self, key: str, value):
        """产品变更时的处理"""
        if key == 'current_product':
            self._try_initialize_directory()
    
    def _try_initialize_directory(self):
        """尝试初始化目录"""
        try:
            current_product = self._shared_data.get_data('current_product')
            if current_product and not self._initialized:
                product_name = current_product.get('model_name', 'DefaultProduct')
                
                # 获取产品特定的自动化监控目录
                product_path = self._path_manager.get_product_path(product_name)
                self.watch_directory = Path(product_path) / "incoming"
                
                self._initialized = True
                self.logger.info(f"✅ AutomationController 已初始化产品 {product_name} 的监控目录")
        except Exception as e:
            self.logger.error(f"⚠️ AutomationController 初始化失败: {e}")
    
    def _ensure_directory_exists(self):
        """按需创建目录"""
        if not self._initialized:
            self._try_initialize_directory()
        
        if self.watch_directory:
            self.watch_directory.mkdir(parents=True, exist_ok=True)
    
    def start_automation(self):
        """启动自动化"""
        if self.is_automation_enabled:
            self.logger.warning("自动化已在运行")
            return
        
        # 确保目录存在
        self._ensure_directory_exists()
        
        if not self.watch_directory:
            self.logger.error("监控目录未初始化，无法启动自动化")
            return
            
        self.is_automation_enabled = True
        
        # 添加监控目录
        self.file_watcher.addPath(str(self.watch_directory))
        
        # 启动批处理定时器
        self.batch_timer.start(5000)  # 5秒处理一次
        
        self.automation_started.emit()
        self.logger.info(f"自动化已启动，监控目录: {self.watch_directory}")
        
    def stop_automation(self):
        """停止自动化"""
        if not self.is_automation_enabled:
            return
            
        self.is_automation_enabled = False
        
        # 移除监控
        if self.file_watcher.directories():
            self.file_watcher.removePaths(self.file_watcher.directories())
            
        # 停止定时器
        self.batch_timer.stop()
        
        self.automation_stopped.emit()
        self.logger.info("自动化已停止")
        
    def set_watch_directory(self, directory: str):
        """设置监控目录"""
        new_path = Path(directory)
        if new_path.exists() and new_path.is_dir():
            # 移除旧的监控
            if self.file_watcher.directories():
                self.file_watcher.removePaths(self.file_watcher.directories())
                
            # 设置新目录
            self.watch_directory = new_path
            
            # 如果自动化正在运行，添加新的监控
            if self.is_automation_enabled:
                self.file_watcher.addPath(str(self.watch_directory))
                
            self.logger.info(f"监控目录已更改: {self.watch_directory}")
        else:
            self.logger.error(f"无效的目录: {directory}")
            
    def _on_directory_changed(self, path: str):
        """目录变化处理"""
        if not self.is_automation_enabled:
            return
            
        # 扫描新文件
        directory = Path(path)
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                if str(file_path) not in self.processed_files:
                    self.pending_files.append(file_path)
                    self.file_detected.emit(str(file_path))
                    self.logger.info(f"检测到新文件: {file_path.name}")
                    
    def _process_batch(self):
        """批量处理待处理文件"""
        if not self.pending_files:
            return
            
        # 处理所有待处理文件
        processed_count = 0
        for file_path in self.pending_files[:]:  # 复制列表以便修改
            if self._process_file(file_path):
                self.pending_files.remove(file_path)
                self.processed_files.add(str(file_path))
                processed_count += 1
                
        if processed_count > 0:
            self.task_completed.emit(f"已处理 {processed_count} 个文件")
            
    def _process_file(self, file_path: Path) -> bool:
        """处理单个文件"""
        try:
            # 检查文件是否仍在写入中
            if self._is_file_busy(file_path):
                return False
                
            # 这里应该实现具体的文件处理逻辑
            # 例如：解析数据、验证格式、导入数据库等
            
            # 移动到已处理目录
            processed_dir = self.watch_directory.parent / "processed"
            processed_dir.mkdir(exist_ok=True)
            
            new_path = processed_dir / file_path.name
            if new_path.exists():
                # 添加时间戳避免覆盖
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_path = processed_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                
            file_path.rename(new_path)
            
            self.logger.info(f"文件已处理: {file_path.name} -> {new_path}")
            return True
            
        except Exception as e:
            error_msg = f"处理文件失败 {file_path.name}: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
            
    def _is_file_busy(self, file_path: Path) -> bool:
        """检查文件是否正在被其他进程使用"""
        try:
            # 尝试以独占模式打开文件
            with open(file_path, 'rb') as f:
                pass
            return False
        except IOError:
            return True
            
    def process_file_manually(self, file_path: str) -> bool:
        """手动处理指定文件"""
        path = Path(file_path)
        if path.exists() and path.is_file():
            return self._process_file(path)
        else:
            self.logger.error(f"文件不存在: {file_path}")
            return False
            
    def get_automation_status(self) -> Dict:
        """获取自动化状态"""
        return {
            'enabled': self.is_automation_enabled,
            'watch_directory': str(self.watch_directory),
            'file_extensions': self.file_extensions,
            'pending_files': len(self.pending_files),
            'processed_files': len(self.processed_files)
        }
        
    def clear_processed_files(self):
        """清空已处理文件列表"""
        self.processed_files.clear()
        self.logger.info("已处理文件列表已清空")
        
    def set_file_extensions(self, extensions: List[str]):
        """设置监控的文件扩展名"""
        self.file_extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        self.logger.info(f"文件扩展名已更新: {self.file_extensions}")