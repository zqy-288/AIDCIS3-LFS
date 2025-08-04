"""
数据控制器
管理数据的存储、处理和导入导出
"""

from PySide6.QtCore import QObject, Signal
import logging
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd


class DataController(QObject):
    """
    数据控制器
    
    负责：
    1. 数据存储管理
    2. CSV文件导入导出
    3. 数据格式转换
    4. 历史数据管理
    """
    
    # 信号定义
    data_loaded = Signal(list)  # 数据加载完成
    data_saved = Signal(str)   # 数据保存完成
    error_occurred = Signal(str)  # 发生错误
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 获取当前产品相关的数据存储路径
        from src.core.shared_data_manager import SharedDataManager
        from src.models.data_path_manager import DataPathManager
        
        self._shared_data = SharedDataManager()
        self._path_manager = DataPathManager()
        
        # 延迟初始化数据目录，等待产品选择
        self.data_root = None
        self._initialized = False
        
        # 监听产品变更
        self._shared_data.data_changed.connect(self._on_product_changed)
        
        # 尝试初始化当前产品的目录
        self._try_initialize_directory()
        
        # 当前数据
        self.current_data = []
        self.current_hole_id = None
    
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
                
                # 获取产品特定的实时监控数据目录
                product_path = self._path_manager.get_product_path(product_name)
                self.data_root = Path(product_path) / "realtime_monitoring"
                
                self._initialized = True
                self.logger.info(f"✅ DataController 已初始化产品 {product_name} 的数据目录")
        except Exception as e:
            self.logger.error(f"⚠️ DataController 初始化失败: {e}")
    
    def _ensure_directory_exists(self):
        """按需创建目录"""
        if not self._initialized:
            self._try_initialize_directory()
        
        if self.data_root:
            self.data_root.mkdir(parents=True, exist_ok=True)
        
    def save_monitoring_data(self, data: List[Dict], hole_id: str) -> str:
        """保存监控数据"""
        try:
            # 确保目录存在
            self._ensure_directory_exists()
            
            if not self.data_root:
                error_msg = "数据目录未初始化"
                self.logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return ""
            
            # 创建文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{hole_id}_{timestamp}.csv"
            filepath = self.data_root / filename
            
            # 保存为CSV
            if data:
                fieldnames = list(data[0].keys())
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in data:
                        # 转换datetime对象为字符串
                        row_copy = row.copy()
                        if 'timestamp' in row_copy and hasattr(row_copy['timestamp'], 'strftime'):
                            row_copy['timestamp'] = row_copy['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")
                        writer.writerow(row_copy)
                
                self.data_saved.emit(str(filepath))
                self.logger.info(f"数据已保存: {filepath}")
                return str(filepath)
            else:
                self.logger.warning("没有数据可保存")
                return ""
                
        except Exception as e:
            error_msg = f"保存数据失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return ""
            
    def load_csv_data(self, filepath: str) -> List[Dict]:
        """加载CSV数据"""
        try:
            data = []
            path = Path(filepath)
            
            if not path.exists():
                raise FileNotFoundError(f"文件不存在: {filepath}")
                
            # 使用pandas读取CSV
            df = pd.read_csv(filepath)
            
            # 转换为字典列表
            for _, row in df.iterrows():
                data_point = row.to_dict()
                
                # 转换时间戳
                if 'timestamp' in data_point:
                    try:
                        data_point['timestamp'] = pd.to_datetime(data_point['timestamp'])
                    except:
                        pass
                        
                data.append(data_point)
                
            self.current_data = data
            self.data_loaded.emit(data)
            self.logger.info(f"已加载 {len(data)} 条数据从: {filepath}")
            
            return data
            
        except Exception as e:
            error_msg = f"加载数据失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return []
            
    def export_anomaly_data(self, anomaly_list: List[Dict], export_path: str = None) -> str:
        """导出异常数据"""
        try:
            if not export_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"anomaly_data_{timestamp}.csv"
                export_path = self.data_root / "anomalies" / filename
                export_path.parent.mkdir(exist_ok=True)
                
            # 保存异常数据
            if anomaly_list:
                fieldnames = list(anomaly_list[0].keys())
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(anomaly_list)
                    
                self.logger.info(f"异常数据已导出: {export_path}")
                return str(export_path)
            else:
                self.logger.warning("没有异常数据可导出")
                return ""
                
        except Exception as e:
            error_msg = f"导出异常数据失败: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return ""
            
    def get_hole_history(self, hole_id: str) -> List[str]:
        """获取指定孔位的历史文件列表"""
        try:
            pattern = f"{hole_id}_*.csv"
            files = list(self.data_root.glob(pattern))
            
            # 按时间排序
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            return [str(f) for f in files]
            
        except Exception as e:
            self.logger.error(f"获取历史文件失败: {str(e)}")
            return []
            
    def load_hole_statistics(self, hole_id: str) -> Dict:
        """加载孔位统计信息"""
        try:
            stats = {
                'hole_id': hole_id,
                'total_measurements': 0,
                'avg_diameter': 0,
                'min_diameter': 0,
                'max_diameter': 0,
                'std_deviation': 0,
                'anomaly_count': 0
            }
            
            # 获取所有相关文件
            files = self.get_hole_history(hole_id)
            
            all_diameters = []
            
            for file in files:
                data = self.load_csv_data(file)
                diameters = [d.get('diameter', 0) for d in data if 'diameter' in d]
                all_diameters.extend(diameters)
                
            if all_diameters:
                import numpy as np
                stats['total_measurements'] = len(all_diameters)
                stats['avg_diameter'] = np.mean(all_diameters)
                stats['min_diameter'] = np.min(all_diameters)
                stats['max_diameter'] = np.max(all_diameters)
                stats['std_deviation'] = np.std(all_diameters)
                
            return stats
            
        except Exception as e:
            self.logger.error(f"加载统计信息失败: {str(e)}")
            return {}
            
    def clear_old_data(self, days: int = 30):
        """清理旧数据文件"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            
            deleted_count = 0
            for file in self.data_root.glob("*.csv"):
                if file.stat().st_mtime < cutoff_time.timestamp():
                    file.unlink()
                    deleted_count += 1
                    
            self.logger.info(f"已删除 {deleted_count} 个旧数据文件")
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {str(e)}")
            
    def get_data_summary(self) -> Dict:
        """获取数据摘要"""
        try:
            csv_files = list(self.data_root.glob("*.csv"))
            
            total_size = sum(f.stat().st_size for f in csv_files)
            
            return {
                'total_files': len(csv_files),
                'total_size_mb': total_size / (1024 * 1024),
                'data_path': str(self.data_root),
                'oldest_file': min(csv_files, key=lambda f: f.stat().st_mtime).name if csv_files else None,
                'newest_file': max(csv_files, key=lambda f: f.stat().st_mtime).name if csv_files else None
            }
            
        except Exception as e:
            self.logger.error(f"获取数据摘要失败: {str(e)}")
            return {}