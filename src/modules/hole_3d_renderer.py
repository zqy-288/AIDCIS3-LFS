#!/usr/bin/env python3
"""
管孔三维模型渲染器
生成实测管径、最大正误差、最小负误差的三维模型
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patches as patches
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PySide6.QtCore import Qt
import math
import os
import tempfile
from datetime import datetime

class Hole3DRenderer(FigureCanvas):
    """管孔三维模型渲染器"""
    
    def __init__(self, parent=None):
        # 增大图形尺寸以充分利用显示空间
        self.figure = Figure(figsize=(14, 12))
        super().__init__(self.figure)
        self.setParent(parent)

        # 创建单个三维子图，调整位置以充分利用空间
        self.ax = self.figure.add_subplot(111, projection='3d')

        # 应用深色主题
        self.apply_dark_theme()

        # 设置鼠标滚轮缩放
        self.setup_mouse_interaction()

        # 初始化空模型
        self.init_empty_model()

        # 调整布局，减少边距以最大化绘图区域
        self.figure.tight_layout(pad=1.0)

    def setup_mouse_interaction(self):
        """设置鼠标交互功能"""
        # 连接鼠标滚轮事件
        self.mpl_connect('scroll_event', self.on_scroll)

    def on_scroll(self, event):
        """鼠标滚轮缩放事件处理"""
        if event.inaxes != self.ax:
            return

        # 获取当前坐标轴范围
        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()
        cur_zlim = self.ax.get_zlim()

        # 设置缩放因子
        if event.button == 'up':
            scale_factor = 0.9  # 放大
        elif event.button == 'down':
            scale_factor = 1.1  # 缩小
        else:
            return

        # 计算新的坐标轴范围（以中心点缩放）
        x_center = (cur_xlim[0] + cur_xlim[1]) / 2
        y_center = (cur_ylim[0] + cur_ylim[1]) / 2
        z_center = (cur_zlim[0] + cur_zlim[1]) / 2

        x_range = (cur_xlim[1] - cur_xlim[0]) * scale_factor / 2
        y_range = (cur_ylim[1] - cur_ylim[0]) * scale_factor / 2
        z_range = (cur_zlim[1] - cur_zlim[0]) * scale_factor / 2

        # 应用新的坐标轴范围
        self.ax.set_xlim(x_center - x_range, x_center + x_range)
        self.ax.set_ylim(y_center - y_range, y_center + y_range)
        self.ax.set_zlim(z_center - z_range, z_center + z_range)
        self.draw()

    def apply_dark_theme(self):
        """应用深色主题到3D图表"""
        # 设置图形背景色（使用更深的主背景色）
        self.figure.patch.set_facecolor('#2C313C')
        self.ax.set_facecolor('#2C313C')

        # 设置坐标轴面板颜色（兼容不同版本的matplotlib）
        try:
            # 新版本matplotlib
            self.ax.xaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
            self.ax.yaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
            self.ax.zaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
        except AttributeError:
            try:
                # 旧版本matplotlib
                self.ax.w_xaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
                self.ax.w_yaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
                self.ax.w_zaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
            except AttributeError:
                # 如果都不支持，跳过面板颜色设置
                pass

        # 设置坐标轴刻度和标签颜色
        self.ax.tick_params(axis='x', colors='#D3D8E0')
        self.ax.tick_params(axis='y', colors='#D3D8E0')
        self.ax.tick_params(axis='z', colors='#D3D8E0')

        self.ax.xaxis.label.set_color('#D3D8E0')
        self.ax.yaxis.label.set_color('#D3D8E0')
        self.ax.zaxis.label.set_color('#D3D8E0')
        self.ax.title.set_color('#FFFFFF')

    def init_empty_model(self):
        """初始化空的三维模型"""
        self.ax.clear()
        self.ax.set_xlabel('X (mm)', fontsize=12)
        self.ax.set_ylabel('Y (mm)', fontsize=12)
        self.ax.set_zlabel('深度 (mm)', fontsize=12)

        # self.ax.set_title('管孔三维模型对比', fontsize=14, fontweight='bold')

        # 设置坐标轴范围
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.set_zlim(0, 100)

        # 设置视角
        self.ax.view_init(elev=20, azim=45)

        # 设置网格
        self.ax.grid(True, alpha=0.3)

        self.draw()
    
    def generate_3d_hole_models(self, measurements):
        """生成合并的三维管孔模型"""
        if not measurements:
            self.init_empty_model()
            return

        # 清除之前的图例引用（如果存在）
        if hasattr(self, '_legend_text_box'):
            delattr(self, '_legend_text_box')

        # 保存当前测量数据，供reset_view使用
        self._current_measurements = measurements

        # 提取数据
        depths = []
        diameters = []

        for measurement in measurements:
            depth = measurement.get('position', measurement.get('depth', 0))
            diameter = measurement.get('diameter', 0)
            depths.append(depth)
            diameters.append(diameter)

        if not depths or not diameters:
            self.init_empty_model()
            return

        # 转换为numpy数组并排序
        depths = np.array(depths)
        diameters = np.array(diameters)

        # 按深度排序
        sort_indices = np.argsort(depths)
        depths = depths[sort_indices]
        diameters = diameters[sort_indices]

        # 标准参数
        standard_diameter = 17.6
        upper_tolerance = 0.05
        lower_tolerance = 0.07

        # 计算误差
        errors = diameters - standard_diameter
        max_positive_error = np.max(errors[errors > 0]) if np.any(errors > 0) else 0
        min_negative_error = np.min(errors[errors < 0]) if np.any(errors < 0) else 0

        # 在单个图中渲染所有模型
        self.render_combined_hole_models(depths, diameters, standard_diameter,
                                       upper_tolerance, lower_tolerance,
                                       max_positive_error, min_negative_error)

        self.draw()

    def render_combined_hole_models(self, depths, diameters, standard_diameter,
                                   upper_tolerance, lower_tolerance,
                                   max_positive_error, min_negative_error):
        """在单个图中渲染所有三维模型"""
        self.ax.clear()
        # 清除后重新应用深色主题
        self.apply_dark_theme()

        # 生成圆柱面参数，增加分辨率以提高模型精度
        theta = np.linspace(0, 2*np.pi, 48)  # 增加角度分辨率
        z_range = np.linspace(np.min(depths), np.max(depths), 80)  # 增加深度分辨率
        Z, THETA = np.meshgrid(z_range, theta)

        # 1. 绘制上公差管径模型（鲜明的红色，增强对比度）
        upper_diameter = standard_diameter + upper_tolerance
        R_upper = np.full_like(Z, upper_diameter / 2)
        X_upper = R_upper * np.cos(THETA)
        Y_upper = R_upper * np.sin(THETA)

        surf_upper = self.ax.plot_surface(X_upper, Y_upper, Z,
                                        alpha=0.4, color='crimson',  # 使用更鲜明的红色
                                        linewidth=0.5, edgecolor='darkred',  # 添加边缘线
                                        label=f'上公差 (+{upper_tolerance:.2f}mm)')

        # 2. 绘制下公差管径模型（鲜明的蓝色，增强对比度）
        lower_diameter = standard_diameter - lower_tolerance
        R_lower = np.full_like(Z, lower_diameter / 2)
        X_lower = R_lower * np.cos(THETA)
        Y_lower = R_lower * np.sin(THETA)

        surf_lower = self.ax.plot_surface(X_lower, Y_lower, Z,
                                        alpha=0.4, color='royalblue',  # 使用更鲜明的蓝色
                                        linewidth=0.5, edgecolor='darkblue',  # 添加边缘线
                                        label=f'下公差 (-{lower_tolerance:.2f}mm)')

        # 3. 绘制实测管径模型（根据公差状态着色，增强视觉效果）
        # 插值实测直径数据
        Z_measured, THETA_measured = np.meshgrid(depths, theta)
        R_measured = np.zeros_like(Z_measured)

        for i, depth in enumerate(depths):
            R_measured[:, i] = diameters[i] / 2

        X_measured = R_measured * np.cos(THETA_measured)
        Y_measured = R_measured * np.sin(THETA_measured)

        # 根据公差状态着色，使用明确的颜色区分
        colors = np.zeros_like(R_measured, dtype=int)
        for i, diameter in enumerate(diameters):
            error = diameter - standard_diameter
            if error > upper_tolerance:  # 超上公差
                colors[:, i] = 2  # 红色索引
            elif error < -lower_tolerance:  # 超下公差
                colors[:, i] = 0  # 蓝色索引
            else:
                colors[:, i] = 1  # 绿色索引

        # 绘制实测表面，使用自定义颜色映射确保绿色明显
        # 创建自定义颜色映射：蓝色-绿色-红色
        from matplotlib.colors import ListedColormap
        import matplotlib.colors as mcolors

        # 使用更鲜明的颜色
        custom_colors = ['blue', 'lime', 'red']  # 使用更亮的绿色
        custom_cmap = ListedColormap(custom_colors)

        # 将颜色索引转换为RGBA颜色
        face_colors = custom_cmap(colors.flatten()).reshape(colors.shape + (4,))

        surf_measured = self.ax.plot_surface(X_measured, Y_measured, Z_measured,
                                           facecolors=face_colors,
                                           alpha=0.9, linewidth=0.3,
                                           edgecolor='black', antialiased=True)

        # 设置坐标轴，增大字体以提高可读性
        self.ax.set_xlabel('X (mm)', fontsize=14, fontweight='bold')
        self.ax.set_ylabel('Y (mm)', fontsize=14, fontweight='bold')
        self.ax.set_zlabel('深度 (mm)', fontsize=14, fontweight='bold')
        # 修改标题字体大小并增加顶部边距以确保完整显示
        self.ax.set_title('管孔三维模型对比', fontsize=15, fontweight='bold', pad=40)

        # 优化坐标轴范围，减少边距以放大模型显示
        max_radius = max(upper_diameter, np.max(diameters)) / 2 * 1.05  # 减少边距从1.2到1.05
        self.ax.set_xlim(-max_radius, max_radius)
        self.ax.set_ylim(-max_radius, max_radius)
        self.ax.set_zlim(np.min(depths), np.max(depths))

        # 优化视角，使模型更加突出
        self.ax.view_init(elev=25, azim=35)  # 调整仰角和方位角

        # 清除之前的图例信息
        if hasattr(self, '_legend_text_box'):
            self._legend_text_box.remove()

        # 添加图例信息（文本框形式），使用更清晰的颜色说明
        legend_text = f"""模型说明:
* 深红色半透明: 上公差 (+{upper_tolerance:.2f}mm)
* 蓝色半透明: 下公差 (-{lower_tolerance:.2f}mm)
* 彩色表面: 实测管径
  - 红色区域: 超上公差
  - 明亮绿色区域: 合格范围
  - 蓝色区域: 超下公差

误差统计:
* 最大正误差: +{max_positive_error:.3f}mm
* 最小负误差: {min_negative_error:.3f}mm"""

        # 将图例移动到右上角位置，增大字体
        # 对于3D坐标轴，使用text2D方法在2D平面上显示文本
        self._legend_text_box = self.ax.text2D(1.02, 0.98, legend_text,
                                             transform=self.ax.transAxes,
                                             bbox=dict(boxstyle='round,pad=1.0',
                                                     facecolor='#3A404E',  # 深色主题背景
                                                     alpha=0.9,
                                                     edgecolor='#505869',  # 深色主题边框
                                                     linewidth=1),
                                             verticalalignment='top',
                                             horizontalalignment='left',
                                             fontsize=12, fontweight='heavy',
                                             color='#D3D8E0')  # 深色主题文字颜色

        # 设置网格，增强可见性
        self.ax.grid(True, alpha=0.4, linewidth=0.8)

        # 设置坐标轴刻度字体大小
        self.ax.tick_params(axis='x', labelsize=11)
        self.ax.tick_params(axis='y', labelsize=11)
        self.ax.tick_params(axis='z', labelsize=11)

        # 调整布局以确保图例不被裁剪，为右侧图例留出空间，最大化绘图区域
        # 为标题留出更多顶部空间，确保标题完全显示
        self.figure.tight_layout(rect=[0, 0, 0.82, 0.95])

    def clear_models(self):
        """清除所有模型"""
        # 安全地清除图例文本框引用
        if hasattr(self, '_legend_text_box'):
            try:
                # 不需要手动remove，ax.clear()会清除所有内容
                delattr(self, '_legend_text_box')
            except Exception as e:
                print(f"清除图例引用时出错（忽略）: {e}")

        # 清除当前测量数据引用
        if hasattr(self, '_current_measurements'):
            delattr(self, '_current_measurements')

        self.init_empty_model()

    def reset_view(self):
        """重置视图到初始状态"""
        # 恢复优化后的默认视角
        self.ax.view_init(elev=25, azim=35)

        # 如果有模型数据，重新计算合适的坐标轴范围
        if hasattr(self, '_current_measurements') and self._current_measurements:
            measurements = self._current_measurements
            # 重新计算坐标轴范围
            diameters = [m.get('diameter', 17.6) for m in measurements]
            depths = [m.get('position', m.get('depth', i)) for i, m in enumerate(measurements)]

            # 设置坐标轴范围，减少边距以放大模型
            max_radius = max(17.65, max(diameters)) / 2 * 1.05  # 减少边距
            self.ax.set_xlim(-max_radius, max_radius)
            self.ax.set_ylim(-max_radius, max_radius)
            self.ax.set_zlim(min(depths), max(depths))
        else:
            # 如果没有数据，使用默认范围
            self.ax.set_xlim(-10, 10)
            self.ax.set_ylim(-10, 10)
            self.ax.set_zlim(0, 100)

        # 重新绘制
        self.draw()
    
    def save_screenshot(self, file_path=None):
        """保存三维模型的截图"""
        if file_path is None:
            # 生成临时文件路径
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"3d_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        try:
            # 保存当前三维模型为PNG文件
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight', 
                               facecolor='#2C313C', edgecolor='none')
            print(f"✅ 三维模型截图已保存: {file_path}")
            return file_path
        except Exception as e:
            print(f"❌ 保存三维模型截图失败: {e}")
            return None



class Hole3DViewer(QWidget):
    """管孔三维模型查看器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 三维渲染器
        self.renderer = Hole3DRenderer()
        layout.addWidget(self.renderer)
        
    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # 标题
        title_label = QLabel("管孔三维模型渲染")
        title_label.setObjectName("Model3DTitle")  # 使用专用样式
        layout.addWidget(title_label)
        
        # 视角选择
        layout.addWidget(QLabel("视角:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["默认视角", "正视图", "侧视图", "俯视图"])
        self.view_combo.currentTextChanged.connect(self.change_view_angle)
        layout.addWidget(self.view_combo)
        
        # 适应视图按钮
        fit_view_btn = QPushButton("适应视图")
        fit_view_btn.clicked.connect(self.fit_view)
        layout.addWidget(fit_view_btn)
        
        layout.addStretch()
        
        return panel
    
    def change_view_angle(self, view_name):
        """改变视角"""
        angles = {
            "默认视角": (20, 45),
            "正视图": (0, 0),
            "侧视图": (0, 90),
            "俯视图": (90, 0)
        }

        if view_name in angles:
            elev, azim = angles[view_name]
            self.renderer.ax.view_init(elev=elev, azim=azim)
            self.renderer.draw()
    
    def fit_view(self):
        """适应视图 - 恢复模型初始导入时的视图和缩放大小"""
        self.renderer.reset_view()

    def clear_models(self):
        """清除模型"""
        self.renderer.clear_models()
    
    def update_models(self, measurements):
        """更新三维模型"""
        self.renderer.generate_3d_hole_models(measurements)
