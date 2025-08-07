#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据文件夹监控服务
自动检测新的RxxxCxxx文件夹并分析数据质量
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
import logging

from PySide6.QtCore import QObject, Signal, QTimer
from ...report_generation_p4.report_generator import ReportGenerator


class DataFolderMonitor(QObject):
    """数据文件夹监控器"""
    
    # 信号定义
    new_hole_detected = Signal(str, dict)  # 新孔位检测到，传递孔位ID和质量数据
    hole_data_updated = Signal(str, dict)  # 孔位数据更新
    monitoring_status_changed = Signal(bool)  # 监控状态变化
    
    def __init__(self, data_root_path: str = "Data", scan_interval: int = 5):
        super().__init__()
        self.data_root_path = Path(data_root_path)
        self.scan_interval = scan_interval  # 扫描间隔（秒）
        self.is_monitoring = False
        
        # 已知的孔位数据
        self.known_holes: Dict[str, dict] = {}
        
        # 报告生成器
        self.report_generator = ReportGenerator()
        
        # 定时器
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.scan_data_folder)
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            return
            
        self.logger.info("🔍 开始监控Data文件夹...")
        self.is_monitoring = True
        
        # 初始扫描
        self.initial_scan()
        
        # 启动定时扫描
        self.scan_timer.start(self.scan_interval * 1000)
        
        self.monitoring_status_changed.emit(True)
        
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
            
        self.logger.info("⏹️ 停止监控Data文件夹")
        self.is_monitoring = False
        
        self.scan_timer.stop()
        self.monitoring_status_changed.emit(False)
        
    def initial_scan(self):
        """初始扫描，建立已知孔位列表"""
        self.logger.info("📊 执行初始扫描...")
        
        try:
            # 扫描所有现有的孔位文件夹
            for hole_dir in self.data_root_path.iterdir():
                if self.is_valid_hole_folder(hole_dir):
                    hole_id = hole_dir.name
                    quality_data = self.analyze_hole_quality(hole_id)
                    if quality_data:
                        self.known_holes[hole_id] = quality_data
                        self.logger.info(f"   📁 已知孔位: {hole_id} (合格率: {quality_data.get('qualification_rate', 0):.1f}%)")
                        
            self.logger.info(f"✅ 初始扫描完成，发现 {len(self.known_holes)} 个孔位")
            
        except Exception as e:
            self.logger.error(f"❌ 初始扫描失败: {e}")
            
    def scan_data_folder(self):
        """扫描数据文件夹，检测新文件夹或数据变化"""
        if not self.is_monitoring:
            return
            
        try:
            current_holes = set()
            
            # 扫描当前存在的孔位文件夹
            for hole_dir in self.data_root_path.iterdir():
                if self.is_valid_hole_folder(hole_dir):
                    hole_id = hole_dir.name
                    current_holes.add(hole_id)
                    
                    # 检查是否是新孔位
                    if hole_id not in self.known_holes:
                        self.handle_new_hole(hole_id)
                    else:
                        # 检查现有孔位是否有数据更新
                        self.check_hole_data_update(hole_id)
                        
            # 检查是否有孔位被删除
            removed_holes = set(self.known_holes.keys()) - current_holes
            for hole_id in removed_holes:
                self.handle_hole_removed(hole_id)
                
        except Exception as e:
            self.logger.error(f"❌ 扫描过程中出现错误: {e}")
            
    def is_valid_hole_folder(self, folder_path: Path) -> bool:
        """检查是否是有效的孔位文件夹"""
        if not folder_path.is_dir():
            return False
            
        folder_name = folder_path.name
        
        # 检查命名格式：R开头且包含C
        if not (folder_name.startswith('R') and 'C' in folder_name):
            return False
            
        # 检查是否包含必要的子目录
        ccidm_dir = folder_path / "CCIDM"
        if not ccidm_dir.exists():
            return False
            
        # 检查是否有CSV文件
        csv_files = list(ccidm_dir.glob("*.csv"))
        if not csv_files:
            return False
            
        return True
        
    def analyze_hole_quality(self, hole_id: str) -> Optional[dict]:
        """分析孔位质量数据"""
        try:
            hole_dir = self.data_root_path / hole_id
            hole_quality_data = self.report_generator._collect_hole_quality_data(hole_id, hole_dir)
            
            if hole_quality_data:
                return {
                    'hole_id': hole_quality_data.hole_id,
                    'qualification_rate': hole_quality_data.qualification_rate,
                    'is_qualified': hole_quality_data.is_qualified,
                    'total_count': hole_quality_data.total_count,
                    'qualified_count': hole_quality_data.qualified_count,
                    'measurement_timestamp': hole_quality_data.measurement_timestamp,
                    'target_diameter': hole_quality_data.target_diameter,
                    'tolerance_upper': hole_quality_data.tolerance_upper,
                    'tolerance_lower': hole_quality_data.tolerance_lower
                }
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 分析孔位 {hole_id} 质量数据失败: {e}")
            return None
            
    def handle_new_hole(self, hole_id: str):
        """处理新检测到的孔位"""
        self.logger.info(f"🆕 检测到新孔位: {hole_id}")
        
        quality_data = self.analyze_hole_quality(hole_id)
        if quality_data:
            self.known_holes[hole_id] = quality_data
            
            # 发送信号通知界面
            self.new_hole_detected.emit(hole_id, quality_data)
            
            # 记录日志
            status = "合格" if quality_data['is_qualified'] else "不合格"
            self.logger.info(f"   📊 {hole_id}: {status} (合格率: {quality_data['qualification_rate']:.1f}%)")
            
    def check_hole_data_update(self, hole_id: str):
        """检查孔位数据是否有更新"""
        try:
            current_data = self.analyze_hole_quality(hole_id)
            if not current_data:
                return
                
            known_data = self.known_holes[hole_id]
            
            # 比较时间戳，检查是否有更新
            if current_data['measurement_timestamp'] > known_data['measurement_timestamp']:
                self.logger.info(f"🔄 孔位 {hole_id} 数据已更新")
                
                self.known_holes[hole_id] = current_data
                self.hole_data_updated.emit(hole_id, current_data)
                
        except Exception as e:
            self.logger.error(f"❌ 检查孔位 {hole_id} 数据更新失败: {e}")
            
    def handle_hole_removed(self, hole_id: str):
        """处理孔位被删除的情况"""
        self.logger.info(f"🗑️ 孔位 {hole_id} 已被删除")
        del self.known_holes[hole_id]
        
    def get_current_summary(self) -> dict:
        """获取当前数据汇总"""
        total_holes = len(self.known_holes)
        qualified_holes = sum(1 for data in self.known_holes.values() if data['is_qualified'])
        unqualified_holes = total_holes - qualified_holes
        qualification_rate = (qualified_holes / total_holes * 100) if total_holes > 0 else 0.0
        
        return {
            'total_holes': total_holes,
            'qualified_holes': qualified_holes,
            'unqualified_holes': unqualified_holes,
            'qualification_rate': qualification_rate,
            'last_update': datetime.now()
        }
        
    def get_unqualified_holes(self) -> List[str]:
        """获取不合格孔位列表"""
        return [hole_id for hole_id, data in self.known_holes.items() if not data['is_qualified']]
        
    def get_qualified_holes(self) -> List[str]:
        """获取合格孔位列表"""
        return [hole_id for hole_id, data in self.known_holes.items() if data['is_qualified']]


# 全局监控器实例
_global_monitor = None

def get_data_monitor() -> DataFolderMonitor:
    """获取全局数据监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = DataFolderMonitor("Data/CAP1000")
    return _global_monitor
