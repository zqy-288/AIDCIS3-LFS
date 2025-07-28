"""
使用matplotlib实现的实时图表组件
替代pyqtgraph，解决误差线显示问题
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QSplitter, QGroupBox, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt, Slot, QTimer
from collections import deque
from .endoscope_view import EndoscopeView


class MatplotlibChart(QWidget):
    """
    使用matplotlib的实时图表组件
    面板A: 管孔直径数据实时折线图（matplotlib）
    面板B: 内窥镜实时图像显示
    """
    
    def __init__(self):
        super().__init__()
        
        # 数据存储
        self.depth_data = deque(maxlen=1000)
        self.diameter_data = deque(maxlen=1000)
        
        # 当前孔号和状态
        self.current_hole = "未设置"
        self.current_depth = 0.0
        self.connection_status = "未连接"
        
        # 标准直径和误差线
        self.standard_diameter = None
        self.max_error_line = None
        self.min_error_line = None
        
        # 设置UI
        self.setup_ui()
        
        # 设置更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_plot)
        self.update_timer.start(100)  # 每100ms更新一次
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建标题
        title_label = QLabel("面板A - 实时管孔直径监测")
        title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #2c3e50; 
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
            margin-bottom: 10px;
        """)
        layout.addWidget(title_label)
        
        # 创建水平分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：图表区域
        chart_widget = self.create_chart_widget()
        splitter.addWidget(chart_widget)
        
        # 右侧：内窥镜视图
        endoscope_widget = self.create_endoscope_widget()
        splitter.addWidget(endoscope_widget)
        
        # 设置分割器比例 (图表:内窥镜 = 7:3)
        splitter.setSizes([700, 300])
        
        # 底部：控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
    def create_chart_widget(self):
        """创建matplotlib图表组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(12, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 创建子图
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Depth (mm)', fontsize=12)
        self.ax.set_ylabel('Diameter (mm)', fontsize=12)
        self.ax.set_title('Real-time Hole Diameter Monitoring', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        
        # 设置初始Y轴范围
        self.ax.set_ylim(16.5, 20.5)
        self.ax.set_xlim(0, 100)
        
        # 初始化数据线
        self.data_line, = self.ax.plot([], [], 'b-', linewidth=2, label='Diameter Data')
        
        # 设置图形样式
        self.figure.tight_layout()
        
        return widget
        
    def create_endoscope_widget(self):
        """创建内窥镜视图组件"""
        widget = QGroupBox("内窥镜实时图像")
        widget.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        
        # 创建内窥镜视图
        self.endoscope_view = EndoscopeView()
        layout.addWidget(self.endoscope_view)
        
        return widget
        
    def create_control_panel(self):
        """创建控制面板"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # 标准直径设置
        diameter_group = QGroupBox("标准直径设置")
        diameter_layout = QHBoxLayout(diameter_group)
        
        diameter_layout.addWidget(QLabel("标准直径:"))
        
        self.standard_diameter_input = QLineEdit()
        self.standard_diameter_input.setPlaceholderText("输入标准直径 (mm)")
        self.standard_diameter_input.setMaximumWidth(150)
        self.standard_diameter_input.returnPressed.connect(self.on_standard_diameter_entered)
        diameter_layout.addWidget(self.standard_diameter_input)
        
        diameter_layout.addWidget(QLabel("mm"))
        
        tolerance_label = QLabel("误差范围: +0.05/-0.07mm")
        tolerance_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        diameter_layout.addWidget(tolerance_label)
        
        layout.addWidget(diameter_group)
        
        # 状态显示
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout(status_group)
        
        self.hole_label = QLabel(f"当前孔号: {self.current_hole}")
        self.depth_label = QLabel(f"当前深度: {self.current_depth:.1f}mm")
        self.status_label = QLabel(f"连接状态: {self.connection_status}")
        
        status_layout.addWidget(self.hole_label)
        status_layout.addWidget(self.depth_label)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        return widget
        
    @Slot()
    def on_standard_diameter_entered(self):
        """处理标准直径输入"""
        try:
            text = self.standard_diameter_input.text().strip()
            if not text:
                # 清除标准直径
                self.clear_standard_diameter()
                return
                
            diameter = float(text)
            if 15.0 <= diameter <= 25.0:  # 合理范围检查
                self.set_standard_diameter(diameter)
            else:
                QMessageBox.warning(self, "输入错误", "标准直径应在15.0-25.0mm范围内")
                self.standard_diameter_input.clear()
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的数字")
            self.standard_diameter_input.clear()
            
    def set_standard_diameter(self, diameter):
        """设置标准直径并绘制误差线"""
        self.standard_diameter = diameter
        
        # 计算误差线位置
        max_error_line_y = diameter + 0.05  # 上限
        min_error_line_y = diameter - 0.07  # 下限
        
        # 移除旧的误差线
        self.remove_error_lines()
        
        # 绘制新的误差线
        self.draw_error_lines(max_error_line_y, min_error_line_y)
        
        # 调整Y轴范围以聚焦标准直径附近
        y_center = diameter
        y_range = 0.15  # ±0.15mm
        self.ax.set_ylim(y_center - y_range, y_center + y_range)
        
        # 更新图表
        self.canvas.draw()
        
        print(f"设置标准直径: {diameter}mm")
        print(f"上误差线: {max_error_line_y:.3f}mm")
        print(f"下误差线: {min_error_line_y:.3f}mm")
        print(f"Y轴范围: {y_center - y_range:.2f} ~ {y_center + y_range:.2f}mm")
        
    def draw_error_lines(self, max_y, min_y):
        """绘制误差线"""
        import time
        start_time = time.time()
        print(f"\n📏 [误差线] 开始绘制误差线...")
        print(f"   • 上限: {max_y:.3f}mm, 下限: {min_y:.3f}mm")
        
        # 获取当前X轴范围
        axis_start = time.time()
        x_min, x_max = self.ax.get_xlim()
        axis_time = time.time() - axis_start
        print(f"   • X轴范围: [{x_min:.1f}, {x_max:.1f}], 获取耗时: {axis_time:.4f}s")
        
        # 绘制上误差线（红色虚线）
        upper_start = time.time()
        self.max_error_line = self.ax.axhline(
            y=max_y, 
            color='red', 
            linestyle='--', 
            linewidth=2, 
            alpha=0.8,
            label=f'Upper Limit {max_y:.2f}mm'
        )
        upper_time = time.time() - upper_start
        print(f"   ✓ 上误差线绘制完成: {upper_time:.4f}s")
        
        # 绘制下误差线（红色虚线）
        lower_start = time.time()
        self.min_error_line = self.ax.axhline(
            y=min_y, 
            color='red', 
            linestyle='--', 
            linewidth=2, 
            alpha=0.8,
            label=f'Lower Limit {min_y:.2f}mm'
        )
        lower_time = time.time() - lower_start
        print(f"   ✓ 下误差线绘制完成: {lower_time:.4f}s")
        
        total_time = time.time() - start_time
        print(f"   ✨ 误差线绘制完成! 总耗时: {total_time:.4f}s")
        
        # 更新图例
        self.ax.legend(loc='upper right')
        
        print(f"matplotlib误差线绘制成功:")
        print(f"  上误差线: y = {max_y:.3f}mm")
        print(f"  下误差线: y = {min_y:.3f}mm")
        
    def remove_error_lines(self):
        """移除误差线"""
        if self.max_error_line:
            self.max_error_line.remove()
            self.max_error_line = None
            
        if self.min_error_line:
            self.min_error_line.remove()
            self.min_error_line = None
            
        # 重置图例
        self.ax.legend([self.data_line], ['Diameter Data'], loc='upper right')
        
    def clear_standard_diameter(self):
        """清除标准直径设置"""
        self.standard_diameter = None
        self.remove_error_lines()
        
        # 恢复默认Y轴范围
        self.ax.set_ylim(16.5, 20.5)
        
        # 更新图表
        self.canvas.draw()
        
        print("清除标准直径，恢复默认Y轴范围: 16.5 - 20.5mm")
        
    def update_data(self, depth, diameter):
        """更新数据点"""
        self.depth_data.append(depth)
        self.diameter_data.append(diameter)
        self.current_depth = depth
        
        # 更新深度标签
        self.depth_label.setText(f"当前深度: {depth:.1f}mm")
        
    def update_plot(self):
        """更新图表显示"""
        import time
        start_time = time.time()
        
        # 初始化计数器
        if not hasattr(self, '_plot_update_count'):
            self._plot_update_count = 0
        self._plot_update_count += 1
        
        if len(self.depth_data) > 0:
            # 更新数据线
            self.data_line.set_data(list(self.depth_data), list(self.diameter_data))
            
            # 动态调整X轴范围
            if len(self.depth_data) > 1:
                x_min = min(self.depth_data)
                x_max = max(self.depth_data)
                x_range = x_max - x_min
                
                if x_range > 0:
                    # 添加一些边距
                    margin = max(x_range * 0.1, 50)
                    self.ax.set_xlim(x_min - margin, x_max + margin)
                else:
                    self.ax.set_xlim(x_min - 50, x_min + 50)
            
            # 重绘画布
            self.canvas.draw_idle()
            
    def update_status(self, hole_name, depth, status):
        """更新状态信息"""
        self.current_hole = hole_name
        self.current_depth = depth
        self.connection_status = status
        
        # 更新状态标签
        self.hole_label.setText(f"当前孔号: {hole_name}")
        self.depth_label.setText(f"当前深度: {depth:.1f}mm")
        self.status_label.setText(f"连接状态: {status}")
        
    def set_current_hole(self, hole_name):
        """设置当前孔号"""
        self.current_hole = hole_name
        self.hole_label.setText(f"当前孔号: {hole_name}")
        
        # 清空数据
        self.depth_data.clear()
        self.diameter_data.clear()
        
        # 重置图表
        self.data_line.set_data([], [])
        self.ax.set_xlim(0, 100)
        self.canvas.draw()
    
    def cleanup(self):
        """清理matplotlib资源"""
        try:
            # 停止定时器
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
                self.update_timer = None
            
            # 安全清理canvas
            if hasattr(self, 'canvas') and self.canvas is not None:
                try:
                    # 先断开所有信号连接
                    self.canvas.mpl_disconnect_all()
                except:
                    pass
                try:
                    # 安全删除canvas
                    self.canvas.close()
                except:
                    pass
                finally:
                    self.canvas = None
            
            # 清除图形内容
            if hasattr(self, 'ax') and self.ax is not None:
                try:
                    self.ax.clear()
                except:
                    pass
                finally:
                    self.ax = None
            
            # 关闭图形
            if hasattr(self, 'figure') and self.figure is not None:
                try:
                    import matplotlib.pyplot as plt
                    plt.close(self.figure)
                except:
                    pass
                finally:
                    self.figure = None
            
            # 清除数据
            if hasattr(self, 'depth_data'):
                self.depth_data.clear()
            if hasattr(self, 'diameter_data'):
                self.diameter_data.clear()
                
        except Exception as e:
            print(f"清理MatplotlibChart时出错: {e}")
    
    def closeEvent(self, event):
        """处理关闭事件"""
        self.cleanup()
        super().closeEvent(event)
