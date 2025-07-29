"""
可视化面板组件
基于重构前的HistoryViewer可视化标签页实现
"""

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel
)
from PySide6.QtCore import Qt, Signal


class HistoryDataPlot(FigureCanvas):
    """历史数据绘图组件 - 基于重构前的实现"""
    
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8))
        super().__init__(self.figure)
        self.setParent(parent)
        
        # 创建一个占满整个区域的坐标图
        self.ax = self.figure.add_subplot(111)
        self.setup_plot_style()
        
        # 数据存储
        self.measurements_data = []
        self.tolerance_data = {}
        
    def setup_plot_style(self):
        """设置图表样式 - 按照重构前的样式"""
        # 应用深色主题
        self.figure.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#1e1e1e')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.tick_params(colors='white')
        for spine in self.ax.spines.values():
            spine.set_color('white')
            
        # 设置标签
        self.ax.set_xlabel('深度 (mm)', fontsize=12, color='white')
        self.ax.set_ylabel('直径 (mm)', fontsize=12, color='white')
        self.ax.set_title('管孔直径测量数据', fontsize=14, color='white', fontweight='bold')
        self.ax.grid(True, alpha=0.3, color='white')
        
    def plot_measurement_data(self, measurements, tolerance_info):
        """绘制测量数据 - 按照重构前的实现"""
        self.measurements_data = measurements
        self.tolerance_data = tolerance_info
        
        # 清除现有图形
        self.ax.clear()
        self.setup_plot_style()
        
        if not measurements:
            self.ax.text(0.5, 0.5, '暂无数据', transform=self.ax.transAxes,
                        ha='center', va='center', fontsize=16, color='gray')
            self.draw()
            return
            
        # 提取数据
        positions = [m.get('position', m.get('depth', 0)) for m in measurements]
        diameters = [m.get('diameter', 0) for m in measurements]
        qualified = [m.get('is_qualified', True) for m in measurements]
        
        # 分离合格和不合格数据点
        qualified_pos = [p for p, q in zip(positions, qualified) if q]
        qualified_dia = [d for d, q in zip(diameters, qualified) if q]
        unqualified_pos = [p for p, q in zip(positions, qualified) if not q]
        unqualified_dia = [d for d, q in zip(diameters, qualified) if not q]
        
        # 绘制数据点
        if qualified_pos:
            self.ax.scatter(qualified_pos, qualified_dia, c='green', s=30, 
                          alpha=0.7, label='合格点', zorder=3)
        if unqualified_pos:
            self.ax.scatter(unqualified_pos, unqualified_dia, c='red', s=30, 
                          alpha=0.7, label='不合格点', zorder=3)
            
        # 绘制连接线
        if positions and diameters:
            self.ax.plot(positions, diameters, 'b-', alpha=0.5, linewidth=1, zorder=2)
            
        # 绘制公差线
        if tolerance_info:
            self.draw_tolerance_lines(tolerance_info, positions)
            
        # 设置坐标轴范围
        if positions and diameters:
            x_margin = (max(positions) - min(positions)) * 0.05
            y_margin = (max(diameters) - min(diameters)) * 0.1
            
            self.ax.set_xlim(min(positions) - x_margin, max(positions) + x_margin)
            self.ax.set_ylim(min(diameters) - y_margin, max(diameters) + y_margin)
            
        # 添加图例
        self.ax.legend(loc='upper right', fancybox=True, shadow=True)
        
        # 刷新图形
        self.draw()
        
    def draw_tolerance_lines(self, tolerance_info, positions):
        """绘制公差线 - 按照重构前的实现"""
        if not positions:
            return
            
        standard_diameter = tolerance_info.get('standard_diameter', 17.73)
        upper_tolerance = tolerance_info.get('upper_tolerance', 0.07)
        lower_tolerance = tolerance_info.get('lower_tolerance', 0.05)
        
        x_min, x_max = min(positions), max(positions)
        
        # 标准直径线
        self.ax.axhline(y=standard_diameter, color='blue', linestyle='-', 
                       linewidth=2, alpha=0.8, label=f'标准直径 {standard_diameter:.2f}mm')
        
        # 上公差线
        upper_limit = standard_diameter + upper_tolerance
        self.ax.axhline(y=upper_limit, color='orange', linestyle='--', 
                       linewidth=2, alpha=0.8, label=f'上限 {upper_limit:.2f}mm')
        
        # 下公差线
        lower_limit = standard_diameter - lower_tolerance
        self.ax.axhline(y=lower_limit, color='orange', linestyle='--', 
                       linewidth=2, alpha=0.8, label=f'下限 {lower_limit:.2f}mm')
        
        # 填充公差区域
        self.ax.fill_between([x_min, x_max], [lower_limit, lower_limit], 
                           [upper_limit, upper_limit], alpha=0.1, color='green')
                           
    def clear_plot(self):
        """清除图表"""
        self.ax.clear()
        self.setup_plot_style()
        self.ax.text(0.5, 0.5, '暂无数据', transform=self.ax.transAxes,
                    ha='center', va='center', fontsize=16, color='gray')
        self.draw()


class Hole3DViewer(QWidget):
    """三维模型查看器占位符 - 按照重构前的设计"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        placeholder = QLabel("三维模型渲染器")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #888;
                background-color: #2b2b2b;
                border: 2px dashed #555;
                border-radius: 8px;
                padding: 50px;
            }
        """)
        
        layout.addWidget(placeholder)
        
    def update_3d_model(self, measurements):
        """更新三维模型 - 占位符实现"""
        print(f"更新三维模型: {len(measurements) if measurements else 0} 个数据点")


class VisualizationPanel(QWidget):
    """
    可视化面板 - 完全按照重构前的设计
    包含二维图表和三维模型标签页
    """

    # 信号定义
    plot_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 检查是否有三维渲染器 - 尝试导入重构前的三维渲染器
        self.has_3d_renderer = self.check_3d_renderer()

        self.setup_ui()

    def check_3d_renderer(self):
        """检查三维渲染器是否可用"""
        try:
            # 尝试导入重构前的三维渲染器
            from ....modules.hole_3d_renderer import Hole3DViewer
            print("✅ 三维渲染器可用")
            return True
        except ImportError as e:
            print(f"⚠️ 三维渲染器不可用: {e}")
            return False
        
    def setup_ui(self):
        """设置用户界面 - 按照重构前的标签页设计"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签页控件 - 按照重构前的设计
        self.tab_widget = QTabWidget()
        
        # 二维图表标签页
        self.plot_widget = HistoryDataPlot()
        self.tab_widget.addTab(self.plot_widget, "二维公差带图表")
        
        # 三维模型标签页
        if self.has_3d_renderer:
            try:
                # 导入并创建真正的三维渲染器
                from ....modules.hole_3d_renderer import Hole3DViewer
                self.model_3d_viewer = Hole3DViewer()
                self.tab_widget.addTab(self.model_3d_viewer, "三维模型渲染")
                print("✅ 三维模型渲染器创建成功")
            except Exception as e:
                print(f"❌ 三维模型渲染器创建失败: {e}")
                # 创建错误提示
                error_label = QLabel(f"三维模型渲染器创建失败\n错误: {str(e)}")
                error_label.setAlignment(Qt.AlignCenter)
                error_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        color: #ff6b6b;
                        background-color: #2b2b2b;
                        border: 2px dashed #ff6b6b;
                        border-radius: 8px;
                        padding: 30px;
                    }
                """)
                self.tab_widget.addTab(error_label, "三维模型渲染")
                self.has_3d_renderer = False
        else:
            # 如果三维渲染器不可用，显示提示
            placeholder = QLabel("三维模型渲染器不可用\n请检查相关依赖")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #888;
                    background-color: #2b2b2b;
                    border: 2px dashed #555;
                    border-radius: 8px;
                    padding: 30px;
                }
            """)
            self.tab_widget.addTab(placeholder, "三维模型渲染")
            
        layout.addWidget(self.tab_widget)
        
    def update_visualization(self, measurements, tolerance_info=None):
        """更新可视化显示 - 按照重构前的实现"""
        # 更新二维图表
        if tolerance_info is None:
            tolerance_info = {
                'standard_diameter': 17.73,
                'upper_tolerance': 0.07,
                'lower_tolerance': 0.05
            }
            
        self.plot_widget.plot_measurement_data(measurements, tolerance_info)
        
        # 更新三维模型（如果可用）
        if self.has_3d_renderer and hasattr(self, 'model_3d_viewer'):
            try:
                # 使用重构前的方法名
                if hasattr(self.model_3d_viewer, 'update_models'):
                    self.model_3d_viewer.update_models(measurements)
                elif hasattr(self.model_3d_viewer, 'update_3d_model'):
                    self.model_3d_viewer.update_3d_model(measurements)
                print(f"✅ 三维模型更新成功: {len(measurements)} 个数据点")
            except Exception as e:
                print(f"❌ 三维模型更新失败: {e}")
            
        self.plot_updated.emit()
        
    def clear_visualization(self):
        """清除可视化显示"""
        self.plot_widget.clear_plot()
        
        if self.has_3d_renderer and hasattr(self, 'model_3d_viewer'):
            self.model_3d_viewer.update_3d_model([])
            
    def export_plot_image(self, file_path):
        """导出图表图像"""
        try:
            self.plot_widget.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            return True
        except Exception as e:
            print(f"导出图表失败: {e}")
            return False
