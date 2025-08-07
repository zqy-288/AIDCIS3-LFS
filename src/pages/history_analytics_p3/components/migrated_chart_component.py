"""
迁移的图表组件 - 高内聚
直接从重构前代码迁移，专门负责二维公差带图表和三维模型渲染
"""

import numpy as np
import matplotlib
try:
    matplotlib.use('Qt5Agg')
except ImportError:
    try:
        matplotlib.use('TkAgg')
    except ImportError:
        matplotlib.use('Agg')

import matplotlib.pyplot as plt

try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    try:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
    except ImportError:
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from matplotlib.figure import Figure
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                               QLabel, QFrame)
from PySide6.QtCore import Qt, Signal

# 配置中文字体 - 直接从重构前迁移
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class MigratedHistoryDataPlot(QWidget):
    """
    迁移的历史数据图表组件 - 高内聚设计
    职责：专门负责二维公差带图表的绘制和显示
    直接从重构前的 HistoryDataPlot 类迁移而来
    """
    
    # 信号定义 - 低耦合通信
    chart_updated = Signal()
    point_clicked = Signal(int, float, float)  # 点击数据点信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.measurements = []
        self.current_hole_id = ""
        
        # 公差参数 - 直接从重构前迁移
        self.standard_diameter = 17.73  # mm
        self.upper_tolerance = 0.07     # +0.07mm
        self.lower_tolerance = 0.05     # -0.05mm
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面 - 直接从重构前代码迁移"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建matplotlib图形 - 直接从重构前迁移
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 设置深色主题 - 直接从重构前迁移
        self.figure.patch.set_facecolor('#313642')
        
        # 初始化空图表
        self.ax = self.figure.add_subplot(111)
        self.setup_chart_style()
        self.show_empty_chart()
        
        # 连接鼠标事件 - 直接从重构前迁移
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        
    def setup_chart_style(self):
        """设置图表样式 - 直接从重构前迁移"""
        self.ax.set_facecolor('#313642')
        
        # 设置坐标轴边框颜色
        for spine in self.ax.spines.values():
            spine.set_color('#505869')
            
        # 设置坐标轴刻度颜色
        self.ax.tick_params(axis='x', colors='#D3D8E0')
        self.ax.tick_params(axis='y', colors='#D3D8E0')
        
        # 设置坐标轴标签颜色
        self.ax.xaxis.label.set_color('#D3D8E0')
        self.ax.yaxis.label.set_color('#D3D8E0')
        self.ax.title.set_color('#FFFFFF')
        
        # 设置网格
        self.ax.grid(True, color='#505869', alpha=0.3)
        
    def show_empty_chart(self):
        """显示空图表 - 直接从重构前迁移"""
        self.ax.clear()
        self.setup_chart_style()
        
        # 设置基本标签和标题
        self.ax.set_xlabel('深度 (mm)', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', fontsize=12)
        self.ax.set_title('二维公差带包络图', fontsize=14, fontweight='bold')
        
        # 显示提示信息
        self.ax.text(0.5, 0.5, '请选择孔位加载数据', 
                    transform=self.ax.transAxes, ha='center', va='center',
                    fontsize=14, color='#888888',
                    bbox=dict(boxstyle='round,pad=0.5', 
                             facecolor='#3a3d45', 
                             edgecolor='#505869',
                             alpha=0.8))
        
        self.canvas.draw()
        
    def plot_data(self, measurements, hole_id=""):
        """绘制数据 - 直接从重构前代码迁移"""
        if not measurements:
            self.show_empty_chart()
            return
            
        self.measurements = measurements
        self.current_hole_id = hole_id
        
        print(f"📊 开始绘制 {hole_id} 的 {len(measurements)} 个数据点")
        
        self.ax.clear()
        self.setup_chart_style()
        
        # 提取数据 - 直接从重构前迁移
        depths = []
        diameters = []
        
        for measurement in measurements:
            # 支持多种键名格式 - 直接从重构前迁移
            depth = measurement.get('position', measurement.get('depth', 0))
            diameter = measurement.get('diameter', 0)
            depths.append(float(depth))
            diameters.append(float(diameter))
            
        if not depths or not diameters:
            self.show_empty_chart()
            return
            
        depths = np.array(depths)
        diameters = np.array(diameters)
        
        # 设置坐标轴范围 - 直接从重构前迁移
        depth_margin = (max(depths) - min(depths)) * 0.05 if len(depths) > 1 else 50
        diameter_margin = (max(diameters) - min(diameters)) * 0.1 if len(diameters) > 1 else 0.05
        
        x_min = max(0, min(depths) - depth_margin)
        x_max = max(depths) + depth_margin
        y_min = min(min(diameters), self.standard_diameter - self.lower_tolerance) - diameter_margin
        y_max = max(max(diameters), self.standard_diameter + self.upper_tolerance) + diameter_margin
        
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        
        # 绘制公差线 - 直接从重构前迁移
        depth_range = [x_min, x_max]
        self.draw_tolerance_lines(depth_range)
        
        # 绘制测量数据曲线 - 直接从重构前迁移
        self.ax.plot(depths, diameters, 'b-', linewidth=2, 
                    marker='o', markersize=4, markerfacecolor='#4A90E2',
                    markeredgecolor='white', markeredgewidth=0.5,
                    label='测量数据', alpha=0.8)
        
        # 标记超出公差的点 - 直接从重构前迁移
        self.mark_outliers(depths, diameters)
        
        # 设置标签和标题
        self.ax.set_xlabel('深度 (mm)', fontsize=12)
        self.ax.set_ylabel('直径 (mm)', fontsize=12)
        
        title = '二维公差带包络图'
        if hole_id:
            title += f' - {hole_id}'
        self.ax.set_title(title, fontsize=14, fontweight='bold')
        
        # 创建图例 - 直接从重构前迁移
        legend = self.ax.legend(loc='upper right', fontsize=10)
        legend.get_frame().set_facecolor('#3a3d45')
        legend.get_frame().set_edgecolor('#505869')
        for text in legend.get_texts():
            text.set_color('#D3D8E0')
            
        # 添加统计信息 - 直接从重构前迁移
        self.add_statistics_textbox(diameters)
        
        self.canvas.draw()
        self.chart_updated.emit()
        
        print(f"✅ 成功绘制图表，数据范围: 深度 {x_min:.1f}-{x_max:.1f}mm, 直径 {y_min:.3f}-{y_max:.3f}mm")
        
    def draw_tolerance_lines(self, depth_range):
        """绘制公差线 - 直接从重构前迁移"""
        # 上公差线
        upper_line = np.full(2, self.standard_diameter + self.upper_tolerance)
        self.ax.plot(depth_range, upper_line, 'r--', linewidth=2, alpha=0.8,
                    label=f'上公差线 ({self.standard_diameter + self.upper_tolerance:.3f}mm)')
        
        # 下公差线 - 注意这里是减法，因为lower_tolerance是正值
        lower_line = np.full(2, self.standard_diameter - self.lower_tolerance)
        self.ax.plot(depth_range, lower_line, 'r--', linewidth=2, alpha=0.8,
                    label=f'下公差线 ({self.standard_diameter - self.lower_tolerance:.3f}mm)')
        
        # 标准直径线
        standard_line = np.full(2, self.standard_diameter)
        self.ax.plot(depth_range, standard_line, 'g-', linewidth=1.5, alpha=0.7,
                    label=f'标准直径 ({self.standard_diameter:.2f}mm)')
        
        # 填充公差带区域
        self.ax.fill_between(depth_range, 
                            self.standard_diameter - self.lower_tolerance,
                            self.standard_diameter + self.upper_tolerance,
                            alpha=0.1, color='green', label='合格区域')
                            
    def mark_outliers(self, depths, diameters):
        """标记超出公差的点 - 直接从重构前迁移"""
        outlier_count = 0
        for i, (depth, diameter) in enumerate(zip(depths, diameters)):
            # 检查是否超出公差
            if (diameter > self.standard_diameter + self.upper_tolerance or 
                diameter < self.standard_diameter - self.lower_tolerance):
                self.ax.plot(depth, diameter, 'ro', markersize=8, alpha=0.9, 
                           markeredgecolor='white', markeredgewidth=1)
                outlier_count += 1
                
        if outlier_count > 0:
            print(f"⚠️ 发现 {outlier_count} 个超出公差的数据点")
            
    def add_statistics_textbox(self, diameters):
        """添加统计信息文本框 - 直接从重构前迁移"""
        if len(diameters) == 0:
            return
            
        # 计算统计量
        mean_diameter = np.mean(diameters)
        std_diameter = np.std(diameters)
        min_diameter = np.min(diameters)
        max_diameter = np.max(diameters)
        
        # 计算合格率
        in_tolerance = np.sum((diameters >= self.standard_diameter - self.lower_tolerance) & 
                             (diameters <= self.standard_diameter + self.upper_tolerance))
        pass_rate = (in_tolerance / len(diameters)) * 100
        
        # 创建统计文本 - 直接从重构前迁移
        stats_text = (
            f'数据统计:\n'
            f'数据点数: {len(diameters)}\n'
            f'平均直径: {mean_diameter:.3f}mm\n'
            f'标准偏差: {std_diameter:.3f}mm\n'
            f'最小值: {min_diameter:.3f}mm\n'
            f'最大值: {max_diameter:.3f}mm\n'
            f'合格率: {pass_rate:.1f}%'
        )
        
        # 添加文本框 - 直接从重构前迁移
        props = dict(boxstyle='round', facecolor='#3a3d45', alpha=0.9, edgecolor='#505869')
        self.ax.text(0.02, 0.98, stats_text, transform=self.ax.transAxes,
                    fontsize=9, verticalalignment='top', bbox=props,
                    color='#D3D8E0')
                    
    def on_click(self, event):
        """处理鼠标点击事件 - 直接从重构前迁移"""
        if event.inaxes != self.ax or not self.measurements:
            return
            
        # 双击重置视图
        if event.dblclick:
            self.reset_view()
            return
            
        # 查找最近的数据点
        if len(self.measurements) > 0:
            click_x = event.xdata
            click_y = event.ydata
            
            if click_x is None or click_y is None:
                return
                
            # 提取深度和直径数据
            depths = [m.get('position', m.get('depth', 0)) for m in self.measurements]
            diameters = [m.get('diameter', 0) for m in self.measurements]
            
            depths = np.array(depths)
            diameters = np.array(diameters)
            
            # 计算到所有数据点的距离
            distances = np.sqrt((depths - click_x)**2 + (diameters - click_y)**2)
            closest_index = np.argmin(distances)
            
            # 如果点击距离足够近，发射信号
            if distances[closest_index] < (max(depths) - min(depths)) * 0.02:
                self.point_clicked.emit(closest_index, 
                                      float(depths[closest_index]), 
                                      float(diameters[closest_index]))
                print(f"📊 点击数据点 {closest_index}: 深度 {depths[closest_index]:.1f}mm, 直径 {diameters[closest_index]:.4f}mm")
                                      
    def on_scroll(self, event):
        """处理鼠标滚轮缩放事件 - 直接从重构前迁移"""
        if event.inaxes != self.ax:
            return
            
        # 获取当前坐标轴范围
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        
        # 获取鼠标位置
        xdata = event.xdata
        ydata = event.ydata
        
        if xdata is None or ydata is None:
            return
            
        # 设置缩放因子
        if event.button == 'up':
            scale_factor = 0.9  # 放大
        elif event.button == 'down':
            scale_factor = 1.1  # 缩小
        else:
            return
            
        # 计算新的坐标轴范围
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        
        new_xlim = [xdata - new_width * (1 - relx), xdata + new_width * relx]
        new_ylim = [ydata - new_height * (1 - rely), ydata + new_height * rely]
        
        # 应用新的坐标轴范围
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw()
        
    def reset_view(self):
        """重置视图 - 直接从重构前迁移"""
        if self.measurements:
            self.plot_data(self.measurements, self.current_hole_id)
        else:
            self.show_empty_chart()
            
    def clear_chart(self):
        """清除图表数据"""
        self.measurements = []
        self.current_hole_id = ""
        self.show_empty_chart()
        
    def export_chart(self, file_path):
        """导出图表为图片"""
        try:
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight', 
                              facecolor=self.figure.get_facecolor())
            print(f"📊 图表已导出: {file_path}")
            return True
        except Exception as e:
            print(f"❌ 图表导出失败: {e}")
            return False
            
    def get_chart_statistics(self):
        """获取图表统计信息"""
        if not self.measurements:
            return {}
            
        diameters = [m.get('diameter', 0) for m in self.measurements]
        diameters = np.array(diameters)
        
        # 计算合格率
        in_tolerance = np.sum((diameters >= self.standard_diameter - self.lower_tolerance) & 
                             (diameters <= self.standard_diameter + self.upper_tolerance))
        
        return {
            'data_count': len(diameters),
            'mean_diameter': np.mean(diameters),
            'std_diameter': np.std(diameters),
            'min_diameter': np.min(diameters),
            'max_diameter': np.max(diameters),
            'pass_rate': (in_tolerance / len(diameters)) * 100,
            'outlier_count': len(diameters) - in_tolerance
        }


class Migrated3DModelViewer(QWidget):
    """
    迁移的三维模型查看器 - 高内聚设计
    职责：专门负责三维模型的渲染和显示
    直接从重构前的 Hole3DViewer 类完整迁移而来
    """
    
    # 信号定义 - 低耦合通信
    model_updated = Signal()
    view_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_measurements = []
        self.current_hole_id = ""
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面 - 完整的三维渲染器"""
        try:
            # 导入三维渲染器
            from .hole_3d_renderer import Hole3DViewer
            
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # 创建三维查看器
            self.viewer_3d = Hole3DViewer()
            layout.addWidget(self.viewer_3d)
            
            # 连接信号
            self.viewer_3d.view_changed.connect(self.view_changed)
            self.viewer_3d.model_reset.connect(self.model_updated)
            
            print("✅ 三维模型渲染器初始化成功")
            
        except ImportError as e:
            print(f"⚠️ 三维渲染器导入失败，使用占位符: {e}")
            self.setup_placeholder_ui()
        except Exception as e:
            print(f"❌ 三维渲染器初始化失败: {e}")
            self.setup_placeholder_ui()
            
    def setup_placeholder_ui(self):
        """设置占位符界面（作为后备方案）"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 占位符标签
        placeholder_label = QLabel("三维模型渲染器暂不可用")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("""
            QLabel {
                color: #888888; 
                font-size: 18px;
                background-color: #2a2d35;
                border: 2px dashed #505869;
                padding: 60px;
                border-radius: 10px;
            }
        """)
        
        layout.addWidget(placeholder_label)
        self.viewer_3d = None
        
    def load_3d_data(self, measurements, hole_id=""):
        """加载三维数据 - 更新三维模型"""
        self.current_measurements = measurements
        self.current_hole_id = hole_id
        
        if hasattr(self, 'viewer_3d') and self.viewer_3d is not None:
            try:
                self.viewer_3d.update_models(measurements)
                self.model_updated.emit()
                print(f"🎯 三维模型已更新: {hole_id}, {len(measurements) if measurements else 0} 条记录")
            except Exception as e:
                print(f"❌ 三维模型更新失败: {e}")
        else:
            print(f"⚠️ 三维渲染器不可用，数据加载跳过: {hole_id}")
            
    def clear_3d_data(self):
        """清除三维数据"""
        if hasattr(self, 'viewer_3d') and self.viewer_3d is not None:
            try:
                self.viewer_3d.clear_models()
                self.current_measurements = []
                self.current_hole_id = ""
                print("🗑️ 三维模型数据已清除")
            except Exception as e:
                print(f"❌ 三维模型清除失败: {e}")


class MigratedChartComponent(QWidget):
    """
    迁移的图表组件容器 - 高内聚设计
    职责：管理二维公差带图表和三维模型渲染的标签页
    直接从重构前的 create_visualization_tabs 方法迁移而来
    """
    
    # 信号定义 - 低耦合通信
    chart_updated = Signal()
    point_clicked = Signal(int, float, float)
    tab_changed = Signal(int, str)  # 标签页切换信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面 - 直接从重构前代码迁移"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建标签页控件 - 直接从重构前迁移
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #505869;
                background-color: #313642;
            }
            QTabBar::tab {
                background-color: #3a3d45;
                color: #D3D8E0;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #505869;
                border-bottom: none;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #4A90E2;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #505869;
            }
        """)
        
        # 二维图表标签页 - 直接从重构前迁移
        self.plot_widget = MigratedHistoryDataPlot()
        self.tab_widget.addTab(self.plot_widget, "二维公差带图表")
        
        # 三维模型标签页 - 直接从重构前迁移
        self.model_3d_viewer = Migrated3DModelViewer()
        self.tab_widget.addTab(self.model_3d_viewer, "三维模型渲染")
        
        # 连接信号
        self.plot_widget.chart_updated.connect(self.chart_updated.emit)
        self.plot_widget.point_clicked.connect(self.point_clicked.emit)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
        
    def on_tab_changed(self, index):
        """标签页切换处理"""
        tab_text = self.tab_widget.tabText(index)
        print(f"📊 切换到标签页: {tab_text}")
        self.tab_changed.emit(index, tab_text)
        
    def load_data(self, measurements, hole_id=""):
        """加载数据到当前活动的标签页"""
        current_index = self.tab_widget.currentIndex()
        
        if current_index == 0:  # 二维图表
            self.plot_widget.plot_data(measurements, hole_id)
        elif current_index == 1:  # 三维模型
            self.model_3d_viewer.load_3d_data(measurements, hole_id)
            
        # 同时加载到两个组件以保持数据同步
        self.plot_widget.plot_data(measurements, hole_id)
        self.model_3d_viewer.load_3d_data(measurements, hole_id)
        
    def clear_data(self):
        """清除所有标签页的数据"""
        self.plot_widget.clear_chart()
        self.model_3d_viewer.clear_3d_data()
        
    def export_current_chart(self, file_path):
        """导出当前活动标签页的图表"""
        current_index = self.tab_widget.currentIndex()
        
        if current_index == 0:  # 二维图表
            return self.plot_widget.export_chart(file_path)
        else:
            print("⚠️ 三维模型导出功能尚未实现")
            return False
            
    def get_chart_statistics(self):
        """获取图表统计信息"""
        return self.plot_widget.get_chart_statistics()
        
    def switch_to_2d_chart(self):
        """切换到二维图表标签页"""
        self.tab_widget.setCurrentIndex(0)
        
    def switch_to_3d_model(self):
        """切换到三维模型标签页"""
        self.tab_widget.setCurrentIndex(1)
        
    def get_current_tab_name(self):
        """获取当前标签页名称"""
        current_index = self.tab_widget.currentIndex()
        return self.tab_widget.tabText(current_index)


if __name__ == "__main__":
    # 测试组件
    from PySide6.QtWidgets import QApplication
    import sys
    from datetime import datetime
    
    app = QApplication(sys.argv)
    
    # 创建测试数据
    test_measurements = []
    base_diameter = 17.73
    
    for i in range(100):
        position = i * 8.36
        diameter = base_diameter + np.random.normal(0, 0.02)
        
        measurement = {
            'sequence': i + 1,
            'position': position,
            'depth': position,
            'diameter': diameter,
            'channel1': diameter * 1000 + np.random.normal(0, 10),
            'channel2': diameter * 1000 + np.random.normal(0, 10),
            'channel3': diameter * 1000 + np.random.normal(0, 10),
            'is_qualified': abs(diameter - base_diameter) <= 0.06,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'operator': '操作员A',
            'notes': f'测试数据{i+1}'
        }
        test_measurements.append(measurement)
    
    # 创建并测试组件
    chart_component = MigratedChartComponent()
    chart_component.load_data(test_measurements, "TestHole")
    chart_component.show()
    
    print("图表统计:", chart_component.get_chart_statistics())
    
    sys.exit(app.exec())