"""
界面控制器组件 - 高内聚低耦合设计  
职责：负责P3.1界面的业务逻辑控制和组件间通信
基于重构前代码完全恢复控制逻辑
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QFileDialog
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional, Any

from ..services.data_query_service import DataQueryService


class HistoryViewController(QObject):
    """
    历史数据界面控制器 - 高内聚设计
    职责：
    1. 协调各个组件间的交互
    2. 处理用户操作逻辑
    3. 管理界面状态
    4. 调用数据服务
    """
    
    # 信号定义
    data_loaded = Signal(list, str)  # 数据加载完成信号 (measurements, hole_id)
    status_updated = Signal(str)     # 状态更新信号 (status_text)
    error_occurred = Signal(str)     # 错误发生信号 (error_message)
    chart_update_requested = Signal(list, str)  # 图表更新请求 (measurements, hole_id)
    table_update_requested = Signal(list)       # 表格更新请求 (measurements)
    export_completed = Signal(str)   # 导出完成信号 (export_path)
    review_requested = Signal(list)  # 人工复查请求 (unqualified_measurements)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 初始化数据服务
        self.data_service = DataQueryService()
        
        # 当前状态
        self.current_workpiece_id = ""
        self.current_hole_id = ""
        self.current_measurements = []
        self.current_hole_data = {}
        
        # 公差参数 - 基于重构前的实际值（非对称公差）
        self.standard_diameter = 17.73  # mm
        self.upper_tolerance = 0.07     # +0.07mm
        self.lower_tolerance = 0.05     # -0.05mm (这是负公差，实际计算时要减去)
        
        self.logger.info("历史数据界面控制器初始化完成")
    
    def set_workpiece_id(self, workpiece_id: str):
        """设置当前工件ID"""
        self.current_workpiece_id = workpiece_id
        self.logger.info(f"设置工件ID: {workpiece_id}")
        
        # 更新状态显示
        if workpiece_id:
            self.status_updated.emit(f"当前工件: {workpiece_id}")
        else:
            self.status_updated.emit("请选择工件ID")
    
    def get_available_holes(self) -> List[str]:
        """获取可用的孔位列表"""
        try:
            holes = self.data_service.get_available_holes()
            self.logger.info(f"获取到 {len(holes)} 个可用孔位")
            return holes
        except Exception as e:
            self.logger.error(f"获取可用孔位失败: {e}")
            self.error_occurred.emit(f"获取可用孔位失败: {e}")
            return []
    
    def query_hole_data(self, hole_id: str) -> bool:
        """
        查询孔位数据 - 基于重构前的查询逻辑
        返回是否查询成功
        """
        self.logger.info(f"开始查询孔位数据: {hole_id}")
        
        # 验证参数
        if not self.current_workpiece_id:
            self.error_occurred.emit("请选择工件ID")
            return False
            
        if not hole_id:
            self.error_occurred.emit("请选择孔位ID")
            return False
            
        # 验证孔位ID格式
        if not (hole_id.startswith('R') and 'C' in hole_id):
            self.error_occurred.emit("孔ID格式错误，请输入新格式的孔ID，如：R001C001")
            return False
        
        try:
            # 使用数据服务查询数据
            measurements = self.data_service.query_hole_data(hole_id)
            
            if not measurements:
                self.error_occurred.emit(f"孔 {hole_id} 没有找到对应的CSV数据文件")
                self._clear_current_data()
                return False
                
            # 更新当前状态
            self.current_hole_id = hole_id
            self.current_measurements = measurements
            self.current_hole_data = {
                'workpiece_id': self.current_workpiece_id,
                'hole_id': hole_id,
                'measurements': measurements,
                'hole_info': {}
            }
            
            # 发射信号通知各组件更新
            self.data_loaded.emit(measurements, hole_id)
            self.chart_update_requested.emit(measurements, hole_id)
            self.table_update_requested.emit(measurements)
            
            # 添加详细调试信息
            print(f"🔍 控制器查询结果详情:")
            print(f"   孔位ID: {hole_id}")
            print(f"   数据总数: {len(measurements)}")
            if measurements:
                print(f"   前3条数据:")
                for i in range(min(3, len(measurements))):
                    m = measurements[i]
                    print(f"     {i+1}: 位置={m.get('position')}, 直径={m.get('diameter'):.4f}")
                print(f"   最后3条数据:")
                for i in range(max(0, len(measurements)-3), len(measurements)):
                    m = measurements[i]  
                    print(f"     {i+1}: 位置={m.get('position')}, 直径={m.get('diameter'):.4f}")
            
            self.status_updated.emit(f"已加载孔位 {hole_id} 数据，共 {len(measurements)} 条记录")
            
            self.logger.info(f"查询孔位数据成功: {hole_id}, {len(measurements)} 条数据")
            return True
            
        except Exception as e:
            self.logger.error(f"查询孔位数据失败: {e}")
            self.error_occurred.emit(f"查询数据时发生错误: {e}")
            self._clear_current_data()
            return False
    
    def export_data(self) -> bool:
        """
        导出当前数据 - 基于重构前的导出逻辑
        """
        if not self.current_measurements:
            self.error_occurred.emit("没有数据可导出，请先查询数据")
            return False
            
        try:
            # 选择导出路径
            default_filename = f"{self.current_hole_id}_历史数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path, _ = QFileDialog.getSaveFileName(
                None,
                "导出历史数据",
                default_filename,
                "CSV文件 (*.csv);;所有文件 (*)"
            )
            
            if not file_path:
                return False
                
            # 使用数据服务导出数据
            success = self.data_service.export_hole_data(
                self.current_hole_id, 
                Path(file_path), 
                include_statistics=True
            )
            
            if success:
                self.export_completed.emit(file_path)
                self.status_updated.emit(f"数据导出成功: {file_path}")
                self.logger.info(f"数据导出成功: {file_path}")
                return True
            else:
                self.error_occurred.emit("数据导出失败")
                return False
                
        except Exception as e:
            self.logger.error(f"导出数据时发生异常: {e}")
            self.error_occurred.emit(f"导出数据时发生错误: {e}")
            return False
    
    def start_manual_review(self):
        """
        启动人工复查 - 基于重构前的复查逻辑
        """
        if not self.current_measurements:
            self.error_occurred.emit("没有数据可复查，请先查询数据")
            return
            
        try:
            # 筛选不合格的测量数据
            unqualified_measurements = []
            
            for i, measurement in enumerate(self.current_measurements):
                diameter = measurement.get('diameter', 0)
                
                # 检查是否超出公差范围 - 修正非对称公差计算
                upper_limit = self.standard_diameter + self.upper_tolerance  # 17.73 + 0.07 = 17.80
                lower_limit = self.standard_diameter - self.lower_tolerance  # 17.73 - 0.05 = 17.68
                
                if diameter > upper_limit or diameter < lower_limit:
                    unqualified_measurements.append((i, measurement))
                    
            if not unqualified_measurements:
                self.status_updated.emit("所有测量数据都在公差范围内，无需人工复查")
                return
                
            # 发射人工复查请求信号
            self.review_requested.emit(unqualified_measurements)
            self.logger.info(f"启动人工复查，{len(unqualified_measurements)} 个不合格点")
            
        except Exception as e:
            self.logger.error(f"启动人工复查时发生异常: {e}")
            self.error_occurred.emit(f"启动人工复查时发生错误: {e}")
    
    def update_review_results(self, review_results: Dict):
        """
        更新人工复查结果
        review_results: {measurement_index: {'diameter': float, 'reviewer': str, 'review_time': datetime}}
        """
        try:
            # 更新当前测量数据
            updated_count = 0
            for index, review_data in review_results.items():
                if 0 <= index < len(self.current_measurements):
                    self.current_measurements[index].update({
                        'diameter': review_data['diameter'],
                        'reviewer': review_data['reviewer'], 
                        'review_time': review_data['review_time'],
                        'notes': f"人工复查 - {review_data['reviewer']}"
                    })
                    updated_count += 1
                    
            if updated_count > 0:
                # 重新发射数据更新信号
                self.table_update_requested.emit(self.current_measurements)
                self.chart_update_requested.emit(self.current_measurements, self.current_hole_id)
                self.status_updated.emit(f"人工复查完成，更新了 {updated_count} 条数据")
                
            self.logger.info(f"人工复查结果更新完成，更新了 {updated_count} 条数据")
            
        except Exception as e:
            self.logger.error(f"更新人工复查结果时发生异常: {e}")
            self.error_occurred.emit(f"更新复查结果时发生错误: {e}")
    
    def set_tolerance_parameters(self, standard_diameter: float, 
                               upper_tolerance: float, lower_tolerance: float):
        """设置公差参数"""
        self.standard_diameter = standard_diameter
        self.upper_tolerance = upper_tolerance
        self.lower_tolerance = lower_tolerance
        
        self.logger.info(f"公差参数已更新: {standard_diameter}mm (+{upper_tolerance}/-{lower_tolerance})")
        
        # 如果有数据，通知图表更新公差线
        if self.current_measurements:
            self.chart_update_requested.emit(self.current_measurements, self.current_hole_id)
    
    def get_current_statistics(self) -> Dict:
        """获取当前数据的统计信息"""
        if not self.current_measurements:
            return {}
            
        try:
            stats = self.data_service.get_data_statistics(self.current_hole_id)
            return stats
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def clear_data(self):
        """清除当前数据"""
        self._clear_current_data()
        self.status_updated.emit("数据已清除")
        
    def _clear_current_data(self):
        """内部清除数据方法"""
        self.current_hole_id = ""
        self.current_measurements = []
        self.current_hole_data = {}
        
        # 通知组件清除显示
        self.table_update_requested.emit([])
        self.chart_update_requested.emit([], "")
    
    def get_current_hole_data(self) -> Dict:
        """获取当前孔位数据"""
        return self.current_hole_data.copy()
    
    def has_current_data(self) -> bool:
        """检查是否有当前数据"""
        return bool(self.current_measurements)
    
    def get_tolerance_parameters(self) -> Dict:
        """获取当前公差参数"""
        return {
            'standard_diameter': self.standard_diameter,
            'upper_tolerance': self.upper_tolerance,
            'lower_tolerance': self.lower_tolerance
        }