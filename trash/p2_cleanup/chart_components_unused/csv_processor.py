"""
P2 CSV数据处理器
整合自 modules/realtime_chart_p2/components/csv_processor.py
负责CSV文件的监控、解析和数据提取
"""

import csv
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable, Tuple
import logging
import time
import hashlib

from PySide6.QtCore import QObject, Signal, QTimer, QFileSystemWatcher


class CSVDataProcessor(QObject):
    """
    CSV数据处理器
    
    功能：
    1. CSV文件监控和自动加载
    2. 数据解析和格式化
    3. 增量数据读取
    4. 数据验证和清理
    5. 多种CSV格式支持
    """
    
    # 信号定义
    data_loaded = Signal(list, list, list)  # depths, diameters, timestamps
    file_changed = Signal(str)  # 文件变化信号
    error_occurred = Signal(str)  # 错误信号
    processing_progress = Signal(int, int)  # 处理进度 (current, total)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 文件监控
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self._on_file_changed)
        
        # 当前监控的文件
        self.current_file = None
        self.last_modified_time = None
        self.last_file_size = 0
        self.last_processed_line = 0
        
        # 文件哈希，用于检测文件内容变化
        self.file_hash = None
        
        # 数据格式配置
        self.column_mapping = {
            'depth': ['depth', 'z', 'position', '深度', '位置'],
            'diameter': ['diameter', 'width', 'measurement', '直径', '测量值'],
            'timestamp': ['timestamp', 'time', 'datetime', '时间', '时间戳']
        }
        
        # 解析配置
        self.delimiter = ','
        self.decimal_separator = '.'
        self.skip_header_lines = 1
        self.encoding = 'utf-8'
        
        # 数据过滤配置
        self.depth_range = None  # (min, max)
        self.diameter_range = None  # (min, max)
        self.time_range = None  # (start, end)
        
        # 处理统计
        self.processing_stats = {
            'total_files_processed': 0,
            'total_rows_processed': 0,
            'total_errors': 0,
            'last_processing_time': None,
            'average_processing_speed': 0.0  # rows per second
        }
        
        # 定时检查文件变化（备用机制）
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_file_changes)
        self.check_timer.start(1000)  # 每秒检查一次
        
    def set_csv_file(self, file_path: str) -> bool:
        """
        设置要监控的CSV文件
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            bool: 是否成功设置
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            if not file_path.is_file():
                raise ValueError(f"不是有效文件: {file_path}")
                
            # 停止监控当前文件
            if self.current_file:
                self.file_watcher.removePath(str(self.current_file))
                
            # 设置新文件
            self.current_file = file_path
            self.last_modified_time = file_path.stat().st_mtime
            self.last_file_size = file_path.stat().st_size
            self.last_processed_line = 0
            self.file_hash = self._calculate_file_hash(file_path)
            
            # 开始监控新文件
            self.file_watcher.addPath(str(file_path))
            
            # 初始加载
            self.load_data()
            
            self.logger.info(f"开始监控CSV文件: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置CSV文件失败: {e}")
            self.error_occurred.emit(f"设置文件失败: {str(e)}")
            return False
            
    def load_data(self, incremental: bool = False) -> bool:
        """
        加载数据
        
        Args:
            incremental: 是否增量加载
            
        Returns:
            bool: 是否成功加载
        """
        if not self.current_file or not self.current_file.exists():
            self.logger.warning("没有有效的CSV文件")
            return False
            
        try:
            start_time = time.time()
            
            if incremental:
                depths, diameters, timestamps = self._load_incremental_data()
            else:
                depths, diameters, timestamps = self._load_full_data()
                self.last_processed_line = 0
                
            # 数据过滤
            if self.depth_range or self.diameter_range or self.time_range:
                depths, diameters, timestamps = self._filter_data(depths, diameters, timestamps)
                
            # 更新统计
            processing_time = time.time() - start_time
            self._update_processing_stats(len(depths), processing_time)
            
            # 发射数据信号
            if depths and diameters:
                self.data_loaded.emit(depths, diameters, timestamps)
                self.logger.debug(f"加载数据: {len(depths)} 个数据点")
                
            return True
            
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            self.error_occurred.emit(f"数据加载失败: {str(e)}")
            return False
            
    def _load_full_data(self) -> Tuple[List[float], List[float], List[datetime]]:
        """加载完整数据"""
        depths = []
        diameters = []
        timestamps = []
        
        try:
            # 尝试使用pandas读取（更快）
            try:
                df = pd.read_csv(self.current_file, 
                               delimiter=self.delimiter,
                               encoding=self.encoding,
                               skiprows=self.skip_header_lines)
                
                # 自动检测列
                depth_col = self._detect_column(df.columns, 'depth')
                diameter_col = self._detect_column(df.columns, 'diameter')
                timestamp_col = self._detect_column(df.columns, 'timestamp')
                
                if depth_col:
                    depths = self._parse_numeric_column(df[depth_col])
                if diameter_col:
                    diameters = self._parse_numeric_column(df[diameter_col])
                if timestamp_col:
                    timestamps = self._parse_timestamp_column(df[timestamp_col])
                else:
                    # 如果没有时间列，生成时间戳
                    timestamps = [datetime.now() + timedelta(seconds=i) 
                                for i in range(len(depths))]
                    
            except Exception as pandas_error:
                self.logger.warning(f"pandas读取失败，使用csv模块: {pandas_error}")
                depths, diameters, timestamps = self._load_with_csv_module()
                
        except Exception as e:
            self.logger.error(f"加载完整数据失败: {e}")
            raise
            
        return depths, diameters, timestamps
        
    def _load_incremental_data(self) -> Tuple[List[float], List[float], List[datetime]]:
        """增量加载数据"""
        depths = []
        diameters = []
        timestamps = []
        
        try:
            with open(self.current_file, 'r', encoding=self.encoding) as f:
                reader = csv.reader(f, delimiter=self.delimiter)
                
                # 跳过已处理的行
                for _ in range(self.last_processed_line + self.skip_header_lines):
                    try:
                        next(reader)
                    except StopIteration:
                        return depths, diameters, timestamps
                        
                # 读取新数据
                line_count = 0
                for row in reader:
                    try:
                        depth, diameter, timestamp = self._parse_row(row)
                        if depth is not None and diameter is not None:
                            depths.append(depth)
                            diameters.append(diameter)
                            timestamps.append(timestamp or datetime.now())
                            line_count += 1
                            
                    except Exception as row_error:
                        self.logger.warning(f"解析行失败: {row_error}")
                        continue
                        
                self.last_processed_line += line_count
                
        except Exception as e:
            self.logger.error(f"增量加载失败: {e}")
            raise
            
        return depths, diameters, timestamps
        
    def _load_with_csv_module(self) -> Tuple[List[float], List[float], List[datetime]]:
        """使用csv模块加载数据"""
        depths = []
        diameters = []
        timestamps = []
        
        with open(self.current_file, 'r', encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            
            # 跳过标题行
            for _ in range(self.skip_header_lines):
                try:
                    next(reader)
                except StopIteration:
                    break
                    
            # 读取数据
            for row_num, row in enumerate(reader):
                try:
                    depth, diameter, timestamp = self._parse_row(row)
                    if depth is not None and diameter is not None:
                        depths.append(depth)
                        diameters.append(diameter)
                        timestamps.append(timestamp or datetime.now())
                        
                    # 发射进度信号
                    if row_num % 1000 == 0:
                        self.processing_progress.emit(row_num, -1)
                        
                except Exception as row_error:
                    self.logger.warning(f"解析第{row_num}行失败: {row_error}")
                    continue
                    
        return depths, diameters, timestamps
        
    def _parse_row(self, row: List[str]) -> Tuple[Optional[float], Optional[float], Optional[datetime]]:
        """解析单行数据"""
        depth = None
        diameter = None
        timestamp = None
        
        try:
            # 简单的列序解析（假设前3列分别是深度、直径、时间）
            if len(row) >= 2:
                depth = self._parse_number(row[0])
                diameter = self._parse_number(row[1])
                
            if len(row) >= 3:
                timestamp = self._parse_timestamp(row[2])
                
        except Exception as e:
            self.logger.debug(f"解析行失败: {e}")
            
        return depth, diameter, timestamp
        
    def _parse_number(self, value: str) -> Optional[float]:
        """解析数字"""
        if not value or not value.strip():
            return None
            
        try:
            # 处理不同的小数分隔符
            if self.decimal_separator == ',':
                value = value.replace(',', '.')
                
            return float(value.strip())
            
        except ValueError:
            return None
            
    def _parse_timestamp(self, value: str) -> Optional[datetime]:
        """解析时间戳"""
        if not value or not value.strip():
            return None
            
        try:
            # 尝试多种时间格式
            time_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y/%m/%d %H:%M:%S',
                '%d/%m/%Y %H:%M:%S',
                '%Y-%m-%d',
                '%d.%m.%Y %H:%M:%S'
            ]
            
            for fmt in time_formats:
                try:
                    return datetime.strptime(value.strip(), fmt)
                except ValueError:
                    continue
                    
            # 如果都失败，尝试解析ISO格式
            return datetime.fromisoformat(value.strip())
            
        except Exception:
            return None
            
    def _parse_numeric_column(self, series) -> List[float]:
        """解析数值列"""
        values = []
        for value in series:
            try:
                if pd.isna(value):
                    continue
                values.append(float(value))
            except (ValueError, TypeError):
                continue
        return values
        
    def _parse_timestamp_column(self, series) -> List[datetime]:
        """解析时间戳列"""
        timestamps = []
        for value in series:
            try:
                if pd.isna(value):
                    continue
                if isinstance(value, str):
                    parsed_time = self._parse_timestamp(value)
                    if parsed_time:
                        timestamps.append(parsed_time)
                else:
                    timestamps.append(pd.to_datetime(value).to_pydatetime())
            except Exception:
                continue
        return timestamps
        
    def _detect_column(self, columns: List[str], data_type: str) -> Optional[str]:
        """自动检测列名"""
        possible_names = self.column_mapping.get(data_type, [])
        
        for col in columns:
            col_lower = col.lower().strip()
            for possible in possible_names:
                if possible.lower() in col_lower:
                    return col
                    
        return None
        
    def _filter_data(self, depths: List[float], diameters: List[float], 
                    timestamps: List[datetime]) -> Tuple[List[float], List[float], List[datetime]]:
        """过滤数据"""
        filtered_depths = []
        filtered_diameters = []
        filtered_timestamps = []
        
        for depth, diameter, timestamp in zip(depths, diameters, timestamps):
            # 深度范围过滤
            if self.depth_range:
                min_depth, max_depth = self.depth_range
                if depth < min_depth or depth > max_depth:
                    continue
                    
            # 直径范围过滤
            if self.diameter_range:
                min_diameter, max_diameter = self.diameter_range
                if diameter < min_diameter or diameter > max_diameter:
                    continue
                    
            # 时间范围过滤
            if self.time_range:
                start_time, end_time = self.time_range
                if timestamp < start_time or timestamp > end_time:
                    continue
                    
            filtered_depths.append(depth)
            filtered_diameters.append(diameter)
            filtered_timestamps.append(timestamp)
            
        return filtered_depths, filtered_diameters, filtered_timestamps
        
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
            
    def _on_file_changed(self, file_path: str):
        """文件变化处理"""
        if file_path == str(self.current_file):
            self.logger.debug(f"检测到文件变化: {file_path}")
            self.file_changed.emit(file_path)
            
            # 延迟加载，避免文件正在写入
            QTimer.singleShot(500, lambda: self.load_data(incremental=True))
            
    def _check_file_changes(self):
        """定期检查文件变化（备用机制）"""
        if not self.current_file or not self.current_file.exists():
            return
            
        try:
            current_mtime = self.current_file.stat().st_mtime
            current_size = self.current_file.stat().st_size
            
            if (current_mtime != self.last_modified_time or 
                current_size != self.last_file_size):
                
                self.last_modified_time = current_mtime
                self.last_file_size = current_size
                
                # 检查文件内容是否真的变化了
                current_hash = self._calculate_file_hash(self.current_file)
                if current_hash != self.file_hash:
                    self.file_hash = current_hash
                    self._on_file_changed(str(self.current_file))
                    
        except Exception as e:
            self.logger.debug(f"检查文件变化失败: {e}")
            
    def _update_processing_stats(self, row_count: int, processing_time: float):
        """更新处理统计"""
        self.processing_stats['total_files_processed'] += 1
        self.processing_stats['total_rows_processed'] += row_count
        self.processing_stats['last_processing_time'] = processing_time
        
        if processing_time > 0:
            current_speed = row_count / processing_time
            old_speed = self.processing_stats['average_processing_speed']
            
            # 移动平均
            self.processing_stats['average_processing_speed'] = (old_speed * 0.8 + current_speed * 0.2)
            
    # 配置方法
    def set_column_mapping(self, depth_col: str = None, diameter_col: str = None, 
                          timestamp_col: str = None):
        """设置列映射"""
        if depth_col:
            self.column_mapping['depth'] = [depth_col]
        if diameter_col:
            self.column_mapping['diameter'] = [diameter_col]
        if timestamp_col:
            self.column_mapping['timestamp'] = [timestamp_col]
            
    def set_csv_format(self, delimiter: str = ',', decimal_separator: str = '.', 
                      skip_header_lines: int = 1, encoding: str = 'utf-8'):
        """设置CSV格式"""
        self.delimiter = delimiter
        self.decimal_separator = decimal_separator
        self.skip_header_lines = skip_header_lines
        self.encoding = encoding
        
    def set_filters(self, depth_range: Tuple[float, float] = None,
                   diameter_range: Tuple[float, float] = None,
                   time_range: Tuple[datetime, datetime] = None):
        """设置数据过滤器"""
        self.depth_range = depth_range
        self.diameter_range = diameter_range
        self.time_range = time_range
        
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计"""
        return self.processing_stats.copy()
        
    def stop_monitoring(self):
        """停止监控"""
        if self.current_file:
            self.file_watcher.removePath(str(self.current_file))
        self.check_timer.stop()
        
    def resume_monitoring(self):
        """恢复监控"""
        if self.current_file:
            self.file_watcher.addPath(str(self.current_file))
        self.check_timer.start(1000)