"""
数据控制器
负责数据处理、CSV文件读取、数据播放等功能
"""

import os
import csv
import logging
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from collections import deque
from PySide6.QtCore import QObject, Signal, QTimer


class DataController(QObject):
    """
    数据控制器
    处理CSV数据读取、播放和实时数据流
    """
    
    # 信号定义
    data_point_ready = Signal(float, float)  # depth, diameter
    data_loading_progress = Signal(int, int)  # current, total
    data_loaded = Signal(str, int)  # file_path, point_count
    playback_started = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()
    error_occurred = Signal(str)  # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # 日志 - 必须在init_hole_data_mapping之前初始化
        self.logger = logging.getLogger(__name__)

        # 数据存储
        self.csv_data = []  # [(depth, diameter), ...]
        self.current_playback_index = 0
        self.is_playing = False

        # 播放控制
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.play_next_point)
        self.playback_speed = 50  # 播放速度 (ms)

        # 孔位数据映射
        self.hole_data_mapping = {}
        self.init_hole_data_mapping()
        
    def init_hole_data_mapping(self):
        """初始化孔位数据映射"""
        try:
            # 获取项目根目录
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_dir))))
            data_path = Path(project_root) / "Data" / "CAP1000"
            
            # 设置孔位到CSV文件的映射
            self.hole_data_mapping = {
                "AC002R001": str(data_path / "AC002R001" / "CCIDM"),
                "AC004R001": str(data_path / "AC004R001" / "CCIDM"),
                "BC001R001": str(data_path / "BC001R001" / "CCIDM"),
                "BC003R001": str(data_path / "BC003R001" / "CCIDM")
            }
            
            # 设置孔位到图像文件的映射
            self.hole_image_mapping = {
                "AC002R001": str(data_path / "AC002R001" / "BISDM" / "result"),
                "AC004R001": str(data_path / "AC004R001" / "BISDM" / "result"),
                "BC001R001": str(data_path / "BC001R001" / "BISDM" / "result"),
                "BC003R001": str(data_path / "BC003R001" / "BISDM" / "result")
            }
            
            self.logger.info("孔位数据映射初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化孔位数据映射失败: {e}")
            self.error_occurred.emit(f"初始化孔位数据映射失败: {e}")
            
    def load_csv_file(self, file_path: str) -> bool:
        """加载CSV文件"""
        try:
            if not os.path.exists(file_path):
                self.error_occurred.emit(f"CSV文件不存在: {file_path}")
                return False
                
            self.csv_data.clear()
            
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                
                # 跳过标题行
                next(csv_reader, None)
                
                for row_index, row in enumerate(csv_reader):
                    try:
                        if len(row) >= 2:
                            depth = float(row[0])
                            diameter = float(row[1])
                            self.csv_data.append((depth, diameter))
                            
                        # 发射进度信号
                        if row_index % 100 == 0:
                            self.data_loading_progress.emit(row_index, len(self.csv_data))
                            
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"跳过无效行 {row_index}: {row}")
                        continue
                        
            self.current_playback_index = 0
            self.data_loaded.emit(file_path, len(self.csv_data))
            self.logger.info(f"CSV文件加载完成: {file_path}, 数据点数: {len(self.csv_data)}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载CSV文件失败: {e}")
            self.error_occurred.emit(f"加载CSV文件失败: {e}")
            return False
            
    def load_hole_data(self, hole_id: str) -> bool:
        """加载指定孔位的数据"""
        try:
            if hole_id not in self.hole_data_mapping:
                self.error_occurred.emit(f"未知的孔位ID: {hole_id}")
                return False
                
            csv_dir = self.hole_data_mapping[hole_id]
            if not os.path.exists(csv_dir):
                self.error_occurred.emit(f"孔位数据目录不存在: {csv_dir}")
                return False
                
            # 查找CSV文件
            csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
            if not csv_files:
                self.error_occurred.emit(f"孔位目录中没有CSV文件: {csv_dir}")
                return False
                
            # 使用第一个CSV文件
            csv_file_path = os.path.join(csv_dir, csv_files[0])
            return self.load_csv_file(csv_file_path)
            
        except Exception as e:
            self.logger.error(f"加载孔位数据失败: {e}")
            self.error_occurred.emit(f"加载孔位数据失败: {e}")
            return False
            
    def start_playback(self, speed_ms: int = 50):
        """开始数据播放"""
        try:
            if not self.csv_data:
                self.error_occurred.emit("没有可播放的数据")
                return False
                
            self.playback_speed = speed_ms
            self.is_playing = True
            self.current_playback_index = 0
            
            self.playback_timer.start(self.playback_speed)
            self.playback_started.emit()
            self.logger.info(f"开始数据播放，速度: {speed_ms}ms")
            return True
            
        except Exception as e:
            self.logger.error(f"开始播放失败: {e}")
            self.error_occurred.emit(f"开始播放失败: {e}")
            return False
            
    def stop_playback(self):
        """停止数据播放"""
        try:
            self.is_playing = False
            self.playback_timer.stop()
            self.playback_stopped.emit()
            self.logger.info("数据播放已停止")
            
        except Exception as e:
            self.logger.error(f"停止播放失败: {e}")
            
    def pause_playback(self):
        """暂停数据播放"""
        try:
            if self.is_playing:
                self.playback_timer.stop()
                self.is_playing = False
                self.playback_stopped.emit()
                self.logger.info("数据播放已暂停")
                
        except Exception as e:
            self.logger.error(f"暂停播放失败: {e}")
            
    def resume_playback(self):
        """恢复数据播放"""
        try:
            if not self.is_playing and self.csv_data and self.current_playback_index < len(self.csv_data):
                self.is_playing = True
                self.playback_timer.start(self.playback_speed)
                self.playback_started.emit()
                self.logger.info("数据播放已恢复")
                
        except Exception as e:
            self.logger.error(f"恢复播放失败: {e}")
            
    def play_next_point(self):
        """播放下一个数据点"""
        try:
            if not self.is_playing or self.current_playback_index >= len(self.csv_data):
                self.stop_playback()
                self.playback_finished.emit()
                return
                
            depth, diameter = self.csv_data[self.current_playback_index]
            self.data_point_ready.emit(depth, diameter)
            
            self.current_playback_index += 1
            
        except Exception as e:
            self.logger.error(f"播放数据点失败: {e}")
            self.stop_playback()
            
    def set_playback_speed(self, speed_ms: int):
        """设置播放速度"""
        self.playback_speed = max(10, min(1000, speed_ms))  # 限制在10-1000ms之间
        if self.playback_timer.isActive():
            self.playback_timer.setInterval(self.playback_speed)
            
    def get_playback_progress(self) -> Tuple[int, int]:
        """获取播放进度"""
        return self.current_playback_index, len(self.csv_data)
        
    def seek_to_position(self, position: int):
        """跳转到指定位置"""
        if 0 <= position < len(self.csv_data):
            self.current_playback_index = position
            
    def clear_data(self):
        """清除数据"""
        self.stop_playback()
        self.csv_data.clear()
        self.current_playback_index = 0
        self.logger.info("数据已清除")
        
    def get_data_statistics(self) -> Dict[str, float]:
        """获取数据统计信息"""
        if not self.csv_data:
            return {}
            
        depths = [point[0] for point in self.csv_data]
        diameters = [point[1] for point in self.csv_data]
        
        return {
            'total_points': len(self.csv_data),
            'max_depth': max(depths),
            'min_depth': min(depths),
            'max_diameter': max(diameters),
            'min_diameter': min(diameters),
            'avg_diameter': sum(diameters) / len(diameters)
        }
        
    def export_data(self, file_path: str) -> bool:
        """导出数据到CSV文件"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow(['Depth(mm)', 'Diameter(mm)'])
                csv_writer.writerows(self.csv_data)
                
            self.logger.info(f"数据导出完成: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            self.error_occurred.emit(f"导出数据失败: {e}")
            return False
