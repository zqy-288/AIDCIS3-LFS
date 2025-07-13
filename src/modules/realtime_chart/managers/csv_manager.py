"""CSV数据管理器模块"""
import os
import csv
from pathlib import Path
from typing import List, Optional, Tuple
from PySide6.QtCore import QObject, Signal, QTimer


class CSVManager(QObject):
    """
    CSV数据导入和播放管理器
    """
    
    # 信号定义
    data_loaded = Signal(int)  # 数据点数量
    data_point_ready = Signal(float, float)  # depth, diameter
    playback_finished = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # CSV数据相关
        self.csv_data: List[Tuple[float, float]] = []
        self.csv_data_index = 0
        self.is_playing = False
        
        # 播放控制
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self._emit_next_data_point)
        self.playback_interval = 50  # ms
        
        # 文件管理
        self.csv_file_list: List[str] = []
        self.current_file_index = 0
        self.csv_base_path = "Data"
        
        # 孔位到CSV文件的映射
        self.hole_csv_mapping = self._init_hole_csv_mapping()
        
    def _init_hole_csv_mapping(self) -> dict:
        """初始化孔位到CSV文件的映射"""
        return {
            'H00001': [
                'Data/H00001/CCIDM/1-2.0.csv',
                'Data/H00001/CCIDM/1-2.1.csv',
                'Data/H00001/CCIDM/1-2.2.csv',
                'Data/H00001/CCIDM/1-2.3.csv',
                'Data/H00001/CCIDM/1-2.4.csv',
                'Data/H00001/CCIDM/1-2.5.csv',
                'Data/H00001/CCIDM/1-2.6.csv',
                'Data/H00001/CCIDM/1-2.7.csv',
                'Data/H00001/CCIDM/1-2.8.csv',
                'Data/H00001/CCIDM/1-2.9.csv',
            ],
            'H00002': [
                'Data/H00002/CCIDM/2-1.0.csv',
                'Data/H00002/CCIDM/2-1.2.csv',
                'Data/H00002/CCIDM/2-1.4.csv',
                'Data/H00002/CCIDM/2-1.6.csv',
                'Data/H00002/CCIDM/2-1.8.csv',
            ]
        }
        
    def load_csv_file(self, file_path: str) -> bool:
        """加载CSV文件"""
        try:
            self.csv_data.clear()
            self.csv_data_index = 0
            
            with open(file_path, 'r', encoding='utf-8-sig') as csvfile:
                # 跳过前两行（标题）
                next(csvfile)
                next(csvfile)
                
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) >= 2:
                        try:
                            depth = float(row[0])
                            diameter = float(row[1])
                            self.csv_data.append((depth, diameter))
                        except ValueError:
                            continue
                            
            if self.csv_data:
                self.data_loaded.emit(len(self.csv_data))
                return True
            else:
                self.error_occurred.emit(f"CSV文件 {file_path} 中没有有效数据")
                return False
                
        except FileNotFoundError:
            self.error_occurred.emit(f"找不到CSV文件: {file_path}")
            return False
        except Exception as e:
            self.error_occurred.emit(f"加载CSV文件失败: {str(e)}")
            return False
            
    def load_csv_for_hole(self, hole_id: str, file_index: int = 0) -> bool:
        """加载指定孔位的CSV文件"""
        if hole_id in self.hole_csv_mapping:
            file_list = self.hole_csv_mapping[hole_id]
            if 0 <= file_index < len(file_list):
                file_path = file_list[file_index]
                self.csv_file_list = file_list
                self.current_file_index = file_index
                return self.load_csv_file(file_path)
        return False
        
    def start_playback(self, interval: int = 50):
        """开始播放CSV数据"""
        if not self.csv_data:
            self.error_occurred.emit("没有加载CSV数据")
            return
            
        self.playback_interval = interval
        self.is_playing = True
        self.playback_timer.start(interval)
        
    def stop_playback(self):
        """停止播放"""
        self.is_playing = False
        self.playback_timer.stop()
        
    def pause_playback(self):
        """暂停播放"""
        self.is_playing = False
        self.playback_timer.stop()
        
    def resume_playback(self):
        """恢复播放"""
        if self.csv_data and self.csv_data_index < len(self.csv_data):
            self.is_playing = True
            self.playback_timer.start(self.playback_interval)
            
    def reset_playback(self):
        """重置播放位置"""
        self.csv_data_index = 0
        
    def _emit_next_data_point(self):
        """发送下一个数据点"""
        if self.csv_data_index < len(self.csv_data):
            depth, diameter = self.csv_data[self.csv_data_index]
            self.data_point_ready.emit(depth, diameter)
            self.csv_data_index += 1
        else:
            # 播放完成
            self.stop_playback()
            self.playback_finished.emit()
            
    def get_progress(self) -> Tuple[int, int]:
        """获取播放进度"""
        return self.csv_data_index, len(self.csv_data)
        
    def get_available_files_for_hole(self, hole_id: str) -> List[str]:
        """获取指定孔位的可用CSV文件列表"""
        if hole_id in self.hole_csv_mapping:
            return self.hole_csv_mapping[hole_id]
        return []
        
    def load_next_file(self) -> bool:
        """加载下一个文件"""
        if self.csv_file_list and self.current_file_index < len(self.csv_file_list) - 1:
            self.current_file_index += 1
            return self.load_csv_file(self.csv_file_list[self.current_file_index])
        return False
        
    def load_previous_file(self) -> bool:
        """加载上一个文件"""
        if self.csv_file_list and self.current_file_index > 0:
            self.current_file_index -= 1
            return self.load_csv_file(self.csv_file_list[self.current_file_index])
        return False