"""
3.1页面 - 光谱共焦历史数据查看器
允许操作员查询、审查任一已检测孔的光谱共焦内径测量历史数据
"""

import numpy as np
import matplotlib
# 修复后端问题 - 使用PySide6兼容的后端
import threading
try:
    # 如果不是主线程，强制使用Agg后端
    if threading.current_thread() != threading.main_thread():
        matplotlib.use('Agg')
    else:
        matplotlib.use('Qt5Agg')  # 首选Qt5Agg
except ImportError:
    try:
        matplotlib.use('TkAgg')  # 备选TkAgg
    except ImportError:
        matplotlib.use('Agg')  # 最后使用Agg（无GUI）

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 使用统一的字体配置模块
try:
    from .font_config import configure_matplotlib_for_chinese, suppress_font_warnings
    # 配置中文字体并抑制警告
    suppress_font_warnings()
    CHINESE_FONT = configure_matplotlib_for_chinese()
except ImportError:
    # 如果字体配置模块不可用，使用基本配置
    CHINESE_FONT = 'Arial Unicode MS'
    plt.rcParams['font.sans-serif'] = [CHINESE_FONT, 'SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

import os
import platform

# 修复matplotlib后端导入
try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
except ImportError:
    try:
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
    except ImportError:
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.optimize import least_squares
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QLineEdit, QComboBox,
                               QGroupBox, QTableWidget, QTableWidgetItem,
                               QSplitter, QTextEdit, QMessageBox, QCompleter)
from PySide6.QtCore import Qt, Signal, QStringListModel
from PySide6.QtGui import QFont
import csv
import os
import glob
from datetime import datetime

from .models import db_manager


class ProbeCircleFitter:
    """基于探头测量的拟合圆算法 - 根据matlab代码实现"""

    @staticmethod
    def circle_from_polar(p1, p2, p3):
        """
        根据三个极坐标点拟合圆
        p1, p2, p3: [r, theta] 格式的极坐标点
        返回: (xc, yc, D) - 圆心坐标和直径
        """
        # 将极坐标转换为直角坐标
        x1 = p1[0] * np.cos(p1[1])
        y1 = p1[0] * np.sin(p1[1])
        x2 = p2[0] * np.cos(p2[1])
        y2 = p2[0] * np.sin(p2[1])
        x3 = p3[0] * np.cos(p3[1])
        y3 = p3[0] * np.sin(p3[1])

        # 计算分母
        D = 2 * (x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))

        if abs(D) < 1e-10:
            raise ValueError("三点共线，无法拟合圆")

        # 计算平方和
        x1s = x1**2 + y1**2
        x2s = x2**2 + y2**2
        x3s = x3**2 + y3**2

        # 计算圆心坐标
        xc = (x1s*(y2 - y3) + x2s*(y3 - y1) + x3s*(y1 - y2)) / D
        yc = (x1s*(x3 - x2) + x2s*(x1 - x3) + x3s*(x2 - x1)) / D

        # 计算半径和直径
        R = np.sqrt((x1 - xc)**2 + (y1 - yc)**2)
        diameter = 2 * R

        return xc, yc, diameter

    @staticmethod
    def process_channel_data(measure_list, probe_r=18.85, probe_small_r=4):
        """
        处理通道数据，计算拟合圆
        measure_list: [channel1, channel2, channel3] 三个通道的测量值
        probe_r: 探头主圆半径 (mm)
        probe_small_r: 子探头小圆半径 (mm)
        返回: 拟合结果字典
        """
        if len(measure_list) != 3:
            raise ValueError("需要三个通道的测量数据")

        # 三个子探头的方向角度
        theta_list = [0, 2*np.pi/3, 4*np.pi/3]

        # 构建三个极坐标点
        p1 = [probe_r + measure_list[0], theta_list[0]]
        p2 = [probe_r + measure_list[1], theta_list[1]]
        p3 = [probe_r + measure_list[2], theta_list[2]]

        # 拟合圆
        xc, yc, diameter = ProbeCircleFitter.circle_from_polar(p1, p2, p3)
        radius = diameter / 2

        return {
            'center_x': xc,
            'center_y': yc,
            'diameter': diameter,
            'radius': radius,
            'measure_points': [p1, p2, p3],
            'probe_r': probe_r,
            'probe_small_r': probe_small_r,
            'theta_list': theta_list
        }


class CircleFitter:
    """圆形拟合算法"""
    
    @staticmethod
    def fit_circle(x, y):
        """
        使用最小二乘法拟合圆
        返回: (center_x, center_y, radius, residual)
        """
        def calc_R(xc, yc):
            """计算到圆心的距离"""
            return np.sqrt((x - xc)**2 + (y - yc)**2)
        
        def f_2(c):
            """目标函数"""
            Ri = calc_R(*c)
            return Ri - Ri.mean()
        
        # 初始估计
        x_m = np.mean(x)
        y_m = np.mean(y)
        center_estimate = x_m, y_m
        
        # 拟合
        center_2, _ = least_squares(f_2, center_estimate).x, _
        xc_2, yc_2 = center_2
        Ri_2 = calc_R(*center_2)
        R_2 = Ri_2.mean()
        residual = np.sum((Ri_2 - R_2)**2)
        
        return xc_2, yc_2, R_2, residual
    
    @staticmethod
    def generate_circle_points(center_x, center_y, radius, num_points=100):
        """生成圆的点坐标"""
        theta = np.linspace(0, 2*np.pi, num_points)
        x = center_x + radius * np.cos(theta)
        y = center_y + radius * np.sin(theta)
        return x, y


class HistoryDataPlot(FigureCanvas):
    """历史数据绘图组件"""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8))
        super().__init__(self.figure)
        self.setParent(parent)

        # 设置图表的默认字体
        self.figure.patch.set_facecolor('white')

        # 创建四个相同大小的拟合圆图
        self.ax1 = self.figure.add_subplot(221)  # 拟合圆图1
        self.ax2 = self.figure.add_subplot(222)  # 拟合圆图2
        self.ax3 = self.figure.add_subplot(223)  # 拟合圆图3
        self.ax4 = self.figure.add_subplot(224)  # 拟合圆图4

        # 初始化时显示空的坐标图
        self.init_empty_plots()

        self.figure.tight_layout(pad=3.0)

    def init_empty_plots(self):
        """初始化空的坐标图"""
        # 为所有四个拟合圆图设置空的坐标系
        for i, ax in enumerate([self.ax1, self.ax2, self.ax3, self.ax4]):
            ax.clear()
            ax.set_xlim(-1, 1)
            ax.set_ylim(-1, 1)
            ax.set_xlabel('X (mm)')
            ax.set_ylabel('Y (mm)')
            ax.set_title(f'拟合圆图 {i+1}')
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal')
        self.draw()
        
    def plot_measurement_data(self, measurements, hole_info):
        """绘制测量数据 - 查询数据后保持四个空的拟合圆图"""
        # 无论是否有数据，都保持四个空的拟合圆图
        self.init_empty_plots()
        
    def plot_fitted_circle(self, diameters, target_diameter):
        """绘制拟合圆图"""
        if len(diameters) < 3:
            return
            
        # 将直径数据转换为圆周上的点
        # 假设测量点均匀分布在圆周上
        n_points = len(diameters)
        angles = np.linspace(0, 2*np.pi, n_points, endpoint=False)
        
        # 使用平均半径作为基准
        avg_radius = np.mean(diameters) / 2
        
        # 生成测量点坐标
        x_measured = []
        y_measured = []
        for i, diameter in enumerate(diameters):
            radius = diameter / 2
            x = radius * np.cos(angles[i])
            y = radius * np.sin(angles[i])
            x_measured.append(x)
            y_measured.append(y)
            
        x_measured = np.array(x_measured)
        y_measured = np.array(y_measured)
        
        # 拟合圆
        try:
            center_x, center_y, fitted_radius, residual = CircleFitter.fit_circle(x_measured, y_measured)
            
            # 绘制测量点
            self.ax2.scatter(x_measured, y_measured, c='blue', s=50, alpha=0.7, label='测量点')
            
            # 绘制拟合圆
            circle_x, circle_y = CircleFitter.generate_circle_points(center_x, center_y, fitted_radius)
            self.ax2.plot(circle_x, circle_y, 'r-', linewidth=2, label='拟合圆')
            
            # 绘制目标圆
            target_radius = target_diameter / 2
            target_x, target_y = CircleFitter.generate_circle_points(0, 0, target_radius)
            self.ax2.plot(target_x, target_y, 'g--', linewidth=2, label='目标圆')
            
            # 标记圆心
            self.ax2.plot(center_x, center_y, 'ro', markersize=8, label='拟合圆心')
            self.ax2.plot(0, 0, 'go', markersize=8, label='目标圆心')
            
            self.ax2.set_xlabel('X (mm)')
            self.ax2.set_ylabel('Y (mm)')
            self.ax2.set_title(f'拟合圆图\n拟合半径: {fitted_radius:.3f}mm')
            self.ax2.legend()
            self.ax2.grid(True, alpha=0.3)
            self.ax2.set_aspect('equal')
            
        except Exception as e:
            self.ax2.text(0.5, 0.5, f'拟合失败: {str(e)}', 
                         transform=self.ax2.transAxes, ha='center', va='center')
            
    def plot_statistics(self, diameters, target_diameter, tolerance):
        """绘制统计信息"""
        if not diameters:
            return
            
        # 计算统计量
        mean_diameter = np.mean(diameters)
        std_diameter = np.std(diameters)
        min_diameter = np.min(diameters)
        max_diameter = np.max(diameters)
        
        # 合格率
        qualified_count = sum(1 for d in diameters if abs(d - target_diameter) <= tolerance)
        qualification_rate = qualified_count / len(diameters) * 100
        
        # 创建统计文本（使用英文避免字体问题）
        stats_text = f"""Statistics:

Measurement Points: {len(diameters)}
Average Diameter: {mean_diameter:.3f} mm
Standard Deviation: {std_diameter:.3f} mm
Minimum: {min_diameter:.3f} mm
Maximum: {max_diameter:.3f} mm

Target Diameter: {target_diameter:.3f} mm
Tolerance Range: ±{tolerance:.3f} mm
Qualified Points: {qualified_count}
Qualification Rate: {qualification_rate:.1f}%

Deviation Statistics:
Average Deviation: {mean_diameter - target_diameter:.3f} mm
Max Positive Dev: {max_diameter - target_diameter:.3f} mm
Max Negative Dev: {min_diameter - target_diameter:.3f} mm"""

        self.ax4.clear()
        self.ax4.text(0.05, 0.95, stats_text, transform=self.ax4.transAxes,
                     fontsize=10, verticalalignment='top')
        self.ax4.set_xlim(0, 1)
        self.ax4.set_ylim(0, 1)
        self.ax4.axis('off')
        self.ax4.set_title('Statistical Analysis')
        
    def clear_plots(self):
        """清除所有图表"""
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()


class HistoryViewer(QWidget):
    """历史数据查看器 - 3.1页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_hole_data = None
        self.circle_plot_index = 0  # 用于跟踪当前绘制拟合圆的子图索引 (0-3)
        self.setup_ui()
        self.load_workpiece_list()
        
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("光谱共焦历史数据查看器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 查询面板
        self.create_query_panel(layout)
        
        # 主内容区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：数据表格
        self.create_data_table(splitter)
        
        # 右侧：图表显示
        self.plot_widget = HistoryDataPlot()
        splitter.addWidget(self.plot_widget)
        
        # 设置分割器比例
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
    def create_query_panel(self, layout):
        """创建查询面板"""
        query_group = QGroupBox("查询条件")
        query_layout = QGridLayout(query_group)
        
        # 工件ID
        query_layout.addWidget(QLabel("工件ID:"), 0, 0)
        self.workpiece_combo = QComboBox()
        self.workpiece_combo.currentTextChanged.connect(self.on_workpiece_changed)
        query_layout.addWidget(self.workpiece_combo, 0, 1)
        
        # 孔ID - 改为支持模糊搜索的下拉组合框
        query_layout.addWidget(QLabel("孔ID:"), 0, 2)
        self.hole_combo = QComboBox()
        self.hole_combo.setEditable(True)  # 允许编辑
        self.hole_combo.setInsertPolicy(QComboBox.NoInsert)  # 不插入新项目
        self.hole_combo.setPlaceholderText("请选择或输入孔ID，如：H001")

        # 设置模糊搜索功能
        self.hole_completer = QCompleter()
        self.hole_completer.setCaseSensitivity(Qt.CaseInsensitive)  # 不区分大小写
        self.hole_completer.setFilterMode(Qt.MatchContains)  # 包含匹配
        self.hole_combo.setCompleter(self.hole_completer)

        query_layout.addWidget(self.hole_combo, 0, 3)
        
        # 查询按钮
        self.query_button = QPushButton("查询数据")
        self.query_button.clicked.connect(self.query_data)
        query_layout.addWidget(self.query_button, 0, 4)
        
        # 导出按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.clicked.connect(self.export_data)
        query_layout.addWidget(self.export_button, 0, 5)
        
        layout.addWidget(query_group)
        
    def create_data_table(self, splitter):
        """创建数据表格"""
        table_group = QGroupBox("测量数据")
        table_layout = QVBoxLayout(table_group)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(8)
        self.data_table.setHorizontalHeaderLabels([
            "位置(mm)", "直径(mm)", "通道1值(μm)", "通道2值(μm)", "通道3值(μm)", "合格", "时间", "操作员"
        ])
        
        # 设置表格属性
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSortingEnabled(True)

        # 禁用表格编辑
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 连接双击事件
        self.data_table.cellDoubleClicked.connect(self.on_table_double_clicked)

        table_layout.addWidget(self.data_table)
        splitter.addWidget(table_group)
        
    def load_workpiece_list(self):
        """加载工件列表"""
        # 这里简化为添加默认工件
        self.workpiece_combo.addItem("WP-2025-001")
        self.on_workpiece_changed("WP-2025-001")
        
    def on_workpiece_changed(self, workpiece_id):
        """工件选择改变"""
        if not workpiece_id:
            return

        # 加载对应工件的孔位列表
        self.load_hole_list(workpiece_id)

    def load_hole_list(self, workpiece_id):
        """加载指定工件的孔位列表"""
        print(f"🔍 加载工件 {workpiece_id} 的孔位列表...")

        # 清空当前孔位选项
        self.hole_combo.clear()

        # 获取可用的孔位列表
        available_holes = self.get_available_holes(workpiece_id)

        if available_holes:
            # 添加孔位选项到下拉框
            self.hole_combo.addItems(available_holes)

            # 更新自动完成器
            hole_model = QStringListModel(available_holes)
            self.hole_completer.setModel(hole_model)

            print(f"✅ 加载了 {len(available_holes)} 个孔位: {', '.join(available_holes)}")
        else:
            print("⚠️ 未找到可用的孔位")

        # 更新占位符文本
        self.hole_combo.setPlaceholderText(f"请选择{workpiece_id}的孔ID，如：H001")

    def get_available_holes(self, workpiece_id):
        """获取可用的孔位列表"""
        available_holes = []

        try:
            # 方法1: 从数据库获取孔位
            from .models import db_manager
            db_holes = db_manager.get_workpiece_holes(workpiece_id)
            if db_holes:
                for hole in db_holes:
                    available_holes.append(hole.hole_id)
                print(f"📊 从数据库获取到 {len(db_holes)} 个孔位")
        except Exception as e:
            print(f"⚠️ 数据库查询失败: {e}")

        # 方法2: 从文件系统扫描孔位目录
        data_base_dir = "Data"
        if os.path.exists(data_base_dir):
            for item in os.listdir(data_base_dir):
                item_path = os.path.join(data_base_dir, item)
                if os.path.isdir(item_path) and item.startswith('H'):
                    # 检查是否有CCIDM目录（测量数据）
                    ccidm_path = os.path.join(item_path, "CCIDM")
                    if os.path.exists(ccidm_path):
                        csv_files = [f for f in os.listdir(ccidm_path) if f.endswith('.csv')]
                        if csv_files:
                            if item not in available_holes:
                                available_holes.append(item)

            print(f"📁 从文件系统扫描到 {len([h for h in available_holes if h.startswith('H')])} 个孔位目录")

        # 如果没有找到任何孔位，提供默认选项
        if not available_holes:
            available_holes = ["H00001", "H00002", "H00003", "H00004", "H00005"]
            print("🔧 使用默认孔位列表")

        # 排序孔位列表
        available_holes.sort()

        return available_holes

    def query_data(self):
        """查询数据"""
        print("🔍 开始查询数据...")

        workpiece_id = self.workpiece_combo.currentText()
        hole_id = self.hole_combo.currentText().strip()

        print(f"📋 查询参数: 工件ID='{workpiece_id}', 孔ID='{hole_id}'")

        if not workpiece_id or not hole_id:
            print("❌ 查询参数不完整")
            QMessageBox.warning(self, "警告", "请选择工件ID和孔ID")
            return

        # 验证孔ID格式（应该以H开头）
        if not hole_id.upper().startswith('H'):
            print("❌ 孔ID格式错误")
            QMessageBox.warning(self, "警告", "孔ID格式错误，请输入以H开头的孔ID，如：H001")
            return

        print("🔍 开始加载CSV数据...")
        # 从CSV文件加载数据
        measurements = self.load_csv_data_for_hole(hole_id)

        print(f"📊 CSV加载结果: {len(measurements) if measurements else 0} 条数据")

        if not measurements:
            print("❌ 没有找到数据")
            QMessageBox.information(self, "信息", f"孔 {hole_id} 没有找到对应的CSV数据文件")
            self.clear_display()
            return

        try:
            print("🔍 开始更新显示...")
            # 更新显示
            self.update_data_table(measurements)
            print("✅ 数据表格更新成功")

            self.plot_widget.plot_measurement_data(measurements, {})
            print("✅ 图表更新成功")

            print("🔍 设置current_hole_data...")
            self.current_hole_data = {
                'workpiece_id': workpiece_id,
                'hole_id': hole_id,
                'measurements': measurements,
                'hole_info': {}
            }

            print(f"✅ 查询数据成功: 工件ID={workpiece_id}, 孔ID={hole_id}")
            print(f"📊 加载了 {len(measurements)} 条测量数据")
            print(f"🔍 current_hole_data 已设置: {self.current_hole_data is not None}")
            print(f"🔍 current_hole_data 内容: {list(self.current_hole_data.keys()) if self.current_hole_data else 'None'}")

        except Exception as e:
            print(f"❌ 更新显示时出错: {e}")
            import traceback
            traceback.print_exc()

            # 即使图表更新失败，也要设置current_hole_data以支持双击功能
            print("🔍 设置current_hole_data（忽略图表错误）...")
            self.current_hole_data = {
                'workpiece_id': workpiece_id,
                'hole_id': hole_id,
                'measurements': measurements,
                'hole_info': {}
            }
            print(f"✅ current_hole_data 已设置: {self.current_hole_data is not None}")

            QMessageBox.warning(self, "警告", f"数据加载成功，但图表显示出错: {str(e)}")
            return

    def load_csv_data_for_hole(self, hole_id):
        """根据孔ID加载对应的CSV数据"""
        # 修复路径问题：使用相对路径查找CSV文件
        csv_paths = [
            f"Data/{hole_id}/CCIDM",
            f"data/{hole_id}/CCIDM",
            f"cache/{hole_id}",
            f"Data/{hole_id}",
            f"data/{hole_id}"
        ]

        csv_files = []
        csv_dir = None

        # 查找存在的CSV目录
        for path in csv_paths:
            if os.path.exists(path):
                csv_dir = path
                # 查找CSV文件
                for csv_file in os.listdir(path):
                    if csv_file.endswith('.csv'):
                        csv_files.append(os.path.join(path, csv_file))
                if csv_files:
                    break

        if not csv_files:
            print(f"CSV数据目录不存在或无CSV文件，已检查路径: {csv_paths}")
            return []

        # 按时间排序
        csv_files.sort()

        # 选择第一个CSV文件（通常每个孔位只有一个CSV文件）
        selected_file = csv_files[0]
        print(f"为孔ID {hole_id} 选择文件: {selected_file}")

        # 读取CSV文件数据
        return self.read_csv_file(selected_file)

    def read_csv_file(self, file_path):
        """读取CSV文件并返回测量数据"""
        measurements = []

        try:
            # 尝试不同的编码
            encodings = ['gbk', 'gb2312', 'utf-8', 'latin-1']

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        reader = csv.reader(file)
                        headers = next(reader)

                        print(f"成功使用编码 {encoding} 读取文件")
                        print(f"CSV文件列头: {headers}")

                        # 查找列索引 - 根据实际CSV文件结构调整
                        measurement_col = 0  # 第一列是测量序号
                        channel1_col = 1     # 通道1值
                        channel2_col = 2     # 通道2值
                        channel3_col = 3     # 通道3值
                        diameter_col = 4     # 计算直径

                        # 验证列数是否足够
                        if len(headers) < 5:
                            print(f"CSV文件列数不足: {len(headers)} < 5")
                            continue

                        # 读取数据行 - 在同一个with块中
                        for row_num, row in enumerate(reader, start=2):
                            try:
                                if len(row) > max(measurement_col, diameter_col, channel1_col, channel2_col, channel3_col):
                                    position = float(row[measurement_col])  # 测量序号对应位置(mm)
                                    diameter = float(row[diameter_col])
                                    channel1 = float(row[channel1_col])
                                    channel2 = float(row[channel2_col])
                                    channel3 = float(row[channel3_col])

                                    # 判断是否合格（假设标准直径为17.6mm，误差范围±0.1mm）
                                    standard_diameter = 17.6
                                    tolerance = 0.1
                                    is_qualified = abs(diameter - standard_diameter) <= tolerance

                                    # 模拟时间（基于文件修改时间）
                                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                                    # 为每个数据点添加秒数偏移，正确处理分钟进位
                                    total_seconds = file_time.second + (row_num - 2)
                                    additional_minutes = total_seconds // 60
                                    new_seconds = total_seconds % 60

                                    # 计算新的分钟数，也要处理小时进位
                                    total_minutes = file_time.minute + additional_minutes
                                    additional_hours = total_minutes // 60
                                    new_minutes = total_minutes % 60

                                    # 计算新的小时数
                                    new_hours = (file_time.hour + additional_hours) % 24

                                    data_time = file_time.replace(hour=new_hours, minute=new_minutes, second=new_seconds)

                                    measurements.append({
                                        'position': position,
                                        'diameter': diameter,
                                        'channel1': channel1,
                                        'channel2': channel2,
                                        'channel3': channel3,
                                        'is_qualified': is_qualified,
                                        'timestamp': data_time,
                                        'operator': ''  # 暂不显示
                                    })

                            except (ValueError, IndexError) as e:
                                print(f"解析第{row_num}行数据时出错: {e}")
                                continue

                        # 成功读取，跳出编码循环
                        break

                except UnicodeDecodeError:
                    continue
            else:
                print(f"无法使用任何编码读取文件: {file_path}")
                return []

        except Exception as e:
            print(f"读取CSV文件时出错: {e}")
            return []

        print(f"成功读取 {len(measurements)} 条测量数据")
        return measurements
        
    def update_data_table(self, measurements):
        """更新数据表格"""
        self.data_table.setRowCount(len(measurements))

        for row, measurement in enumerate(measurements):
            # 位置(mm) - 对应测量序号
            position = measurement.get('position', measurement.get('depth', 0))
            self.data_table.setItem(row, 0, QTableWidgetItem(f"{position:.1f}"))

            # 直径(mm)
            diameter = measurement.get('diameter', 0)
            self.data_table.setItem(row, 1, QTableWidgetItem(f"{diameter:.4f}"))

            # 通道1值(mm)
            channel1 = measurement.get('channel1', 0)
            self.data_table.setItem(row, 2, QTableWidgetItem(f"{channel1:.2f}"))

            # 通道2值(mm)
            channel2 = measurement.get('channel2', 0)
            self.data_table.setItem(row, 3, QTableWidgetItem(f"{channel2:.2f}"))

            # 通道3值(mm)
            channel3 = measurement.get('channel3', 0)
            self.data_table.setItem(row, 4, QTableWidgetItem(f"{channel3:.2f}"))

            # 合格性
            is_qualified = measurement.get('is_qualified', True)
            qualified_text = "✓" if is_qualified else "✗"
            item = QTableWidgetItem(qualified_text)
            if not is_qualified:
                item.setBackground(Qt.red)
            else:
                item.setBackground(Qt.green)
            self.data_table.setItem(row, 5, item)

            # 时间
            timestamp = measurement.get('timestamp', '')
            if timestamp:
                time_str = timestamp.strftime("%H:%M:%S")
            else:
                time_str = "--"
            self.data_table.setItem(row, 6, QTableWidgetItem(time_str))

            # 操作员
            operator = measurement.get('operator', '--')
            self.data_table.setItem(row, 7, QTableWidgetItem(operator))

        # 调整列宽
        self.data_table.resizeColumnsToContents()
        
    def clear_display(self):
        """清除显示"""
        self.data_table.setRowCount(0)
        self.plot_widget.clear_plots()
        self.plot_widget.draw()
        
    def export_data(self):
        """导出数据"""
        if not self.current_hole_data:
            QMessageBox.warning(self, "警告", "没有数据可导出")
            return

        # 这里可以实现数据导出功能
        QMessageBox.information(self, "信息", "数据导出功能待实现")

    def on_table_double_clicked(self, row, column):
        """处理表格双击事件"""
        print(f"🔍 双击事件触发: 行{row}, 列{column}")

        # 详细检查数据状态
        print(f"🔍 检查数据状态:")
        print(f"   hasattr(self, 'current_hole_data'): {hasattr(self, 'current_hole_data')}")
        if hasattr(self, 'current_hole_data'):
            print(f"   self.current_hole_data is not None: {self.current_hole_data is not None}")
            if self.current_hole_data:
                print(f"   current_hole_data keys: {list(self.current_hole_data.keys())}")
                if 'measurements' in self.current_hole_data:
                    print(f"   measurements count: {len(self.current_hole_data['measurements'])}")

        # 检查是否有数据
        if not hasattr(self, 'current_hole_data') or not self.current_hole_data:
            print("❌ 没有当前孔数据，请先查询数据")
            QMessageBox.warning(self, "提示", "请先查询数据，然后再双击表格行进行拟合圆分析")
            return

        # 检查是否有测量数据
        if 'measurements' not in self.current_hole_data or not self.current_hole_data['measurements']:
            print("❌ 没有测量数据")
            QMessageBox.warning(self, "提示", "当前没有测量数据")
            return

        if row >= self.data_table.rowCount():
            print(f"❌ 行索引超出范围: {row} >= {self.data_table.rowCount()}")
            return

        try:
            # 从数据源获取通道数据（更可靠的方法）
            measurements = self.current_hole_data['measurements']
            if row >= len(measurements):
                print(f"❌ 行索引超出数据范围: {row} >= {len(measurements)}")
                return

            measurement = measurements[row]

            # 提取通道数据
            channel1 = measurement.get('channel1', 0)
            channel2 = measurement.get('channel2', 0)
            channel3 = measurement.get('channel3', 0)

            # 检查通道数据是否有效
            if channel1 == 0 and channel2 == 0 and channel3 == 0:
                QMessageBox.warning(self, "警告", "该行的通道数据为空或无效")
                return

            # 数据转换：通道数据单位为μm，使用公式 2.1 - 通道值*0.001 进行处理
            # 这个公式将μm数据转换为绘图所需的参数，对应matlab.txt中的measure_list数组值
            if channel1 > 100:  # 检测到大数值格式（μm单位）
                # 转换公式：2.1 - 通道值 * 0.001
                # 例如：1385.62μm → 2.1 - 1385.62*0.001 = 2.1 - 1.38562 = 0.71438
                channel1_processed = 2.1 - channel1 * 0.001
                channel2_processed = 2.1 - channel2 * 0.001
                channel3_processed = 2.1 - channel3 * 0.001

                print(f"🔄 数据转换: μm -> 绘图参数")
                print(f"   原始数据(μm): [{measurement.get('channel1'):.2f}, {measurement.get('channel2'):.2f}, {measurement.get('channel3'):.2f}]")
                print(f"   转换公式: 2.1 - 通道值*0.001")
                print(f"   转换后: [{channel1_processed:.6f}, {channel2_processed:.6f}, {channel3_processed:.6f}]")
            else:
                # 如果是小数值，假设已经是处理后的参数
                channel1_processed = channel1
                channel2_processed = channel2
                channel3_processed = channel3
                print(f"🔄 数据已为处理后参数: [{channel1_processed:.6f}, {channel2_processed:.6f}, {channel3_processed:.6f}]")

            measure_list = [channel1_processed, channel2_processed, channel3_processed]

            # 获取位置信息
            position = measurement.get('position', measurement.get('depth', row + 1))

            print(f"✅ 双击第{row+1}行，位置: {position}mm")
            print(f"📊 处理后的绘图参数: {measure_list}")

            # 绘制拟合圆图，传递行号用于动态标题
            print("🎯 开始绘制拟合圆...")
            self.plot_probe_fitted_circles(measure_list, row + 1)  # 传递数据行号
            print("✅ 拟合圆绘制完成")

        except ValueError as e:
            QMessageBox.warning(self, "错误", f"数据格式错误: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理数据时发生错误: {str(e)}")

    def plot_probe_fitted_circles(self, measure_list, data_row_number):
        """
        根据通道数据绘制拟合圆图
        measure_list: [channel1, channel2, channel3] 三个通道的处理后参数
                     处理公式：2.1 - 通道值(μm)*0.001
        data_row_number: 数据行号，用于动态标题
        """
        try:
            print("🔄 开始拟合圆计算...")
            # 使用探头拟合算法处理数据
            result = ProbeCircleFitter.process_channel_data(measure_list)
            # 将measure_list添加到结果中，供绘制函数使用
            result['measure_list'] = measure_list
            print(f"✅ 拟合圆计算成功: 圆心({result['center_x']:.4f}, {result['center_y']:.4f})")

            print(f"🎨 在子图{self.circle_plot_index + 1}绘制拟合圆...")
            # 根据当前索引选择对应的子图绘制拟合圆，传递数据行号
            self.plot_fitted_circle_single(result, self.circle_plot_index, data_row_number)

            # 更新索引，循环使用四个子图 (0->1->2->3->0...)
            self.circle_plot_index = (self.circle_plot_index + 1) % 4
            print(f"✅ 拟合圆绘制完成，下次将绘制在子图{self.circle_plot_index + 1}")

        except Exception as e:
            print(f"❌ 拟合圆计算失败: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"拟合圆计算失败: {str(e)}")

    def plot_fitted_circle_single(self, result, plot_index, data_row_number):
        """在指定的子图上绘制拟合圆 - 按照MATLAB代码逻辑

        Args:
            result: 拟合圆计算结果
            plot_index: 子图索引 (0-3)，对应ax1, ax2, ax3, ax4
            data_row_number: 数据行号，用于动态标题
        """
        # 选择对应的子图
        axes = [self.plot_widget.ax1, self.plot_widget.ax2,
                self.plot_widget.ax3, self.plot_widget.ax4]
        ax = axes[plot_index]

        # 清除当前子图
        ax.clear()

        # 从result中获取measure_list（已处理的通道数据）
        measure_list = result.get('measure_list', [0.714, 0.095, 0.664])

        # 参数定义（按照MATLAB代码）
        probe_r = 8.305              # 探头主圆半径
        probe_small_r = 2           # 子探头小圆半径
        theta_list = [0, 2*np.pi/3, 4*np.pi/3]  # 三个子探头方向

        # 计算三个测量点的极坐标
        p1 = [probe_r + measure_list[0], theta_list[0]]
        p2 = [probe_r + measure_list[1], theta_list[1]]
        p3 = [probe_r + measure_list[2], theta_list[2]]

        # 计算拟合圆参数
        xc, yc, D_target = self.circle_from_polar(p1, p2, p3)
        R_target = D_target / 2

        # 配色定义
        probe_color = [0.2, 0.5, 0.8]     # 蓝色
        measure_color = [0, 0, 0]         # 黑色
        target_color = [0.8, 0.2, 0.2]    # 深红
        radial_color = [0.6, 0.6, 0.6]    # 浅灰

        theta = np.linspace(0, 2*np.pi, 300)

        # 1. 探头主圆（蓝虚线）
        x_probe = probe_r * np.cos(theta)
        y_probe = probe_r * np.sin(theta)
        ax.plot(x_probe, y_probe, '--', color=probe_color, linewidth=1.2, label='探头主圆')
        ax.plot(0, 0, 'o', markersize=4, color=probe_color)
        ax.text(0, 0, ' 探头中心', fontsize=8)

        # 2. 子探头小圆（蓝实线）+ 径向灰虚线 + 测量段
        for i in range(3):
            theta_i = theta_list[i]

            # 子探头圆心
            x_small = (probe_r - probe_small_r) * np.cos(theta_i)
            y_small = (probe_r - probe_small_r) * np.sin(theta_i)
            x_c = x_small + probe_small_r * np.cos(theta)
            y_c = y_small + probe_small_r * np.sin(theta)
            ax.plot(x_c, y_c, '-', color=probe_color, linewidth=1.8)

            # 标注子探头
            ax.plot(x_small, y_small, 'o', markersize=6,
                   markerfacecolor=probe_color, markeredgecolor=probe_color)
            ax.text(x_small, y_small, f'  T{i+1}', fontsize=8, color=probe_color)

            # 径向虚线
            x_end = (probe_r + measure_list[i]) * np.cos(theta_i)
            y_end = (probe_r + measure_list[i]) * np.sin(theta_i)
            ax.plot([0, x_end], [0, y_end], '--', color=radial_color, linewidth=1)

            # 测量段（黑色实线）
            x1 = probe_r * np.cos(theta_i)
            y1 = probe_r * np.sin(theta_i)
            x2 = (probe_r + measure_list[i]) * np.cos(theta_i)
            y2 = (probe_r + measure_list[i]) * np.sin(theta_i)

            ax.plot([x1, x2], [y1, y2], '-', color=measure_color, linewidth=2)
            ax.plot(x2, y2, 'ko', markerfacecolor='k', markersize=5)
            ax.text(x2, y2, f' P{i+1}', fontsize=8)

        # 4. 待测圆（深红）
        x_target = xc + R_target * np.cos(theta)
        y_target = yc + R_target * np.sin(theta)
        ax.plot(x_target, y_target, '-', color=target_color, linewidth=2.5, label='待测圆')
        ax.plot(xc, yc, 'o', markersize=7,
               markerfacecolor=target_color, markeredgecolor=target_color)
        ax.text(xc, yc, '  待测圆心', fontsize=8, color=target_color)

        # 设置图表属性
        ax.set_xlabel('X (mm)', fontsize=9)
        ax.set_ylabel('Y (mm)', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # 动态标题：数据X拟合圆
        ax.set_title(f'数据{data_row_number}拟合圆', fontsize=10, fontweight='bold')

        # 设置合适的显示范围
        max_range = max(probe_r + max(measure_list), R_target + abs(xc), R_target + abs(yc)) * 1.1
        ax.set_xlim(-max_range, max_range)
        ax.set_ylim(-max_range, max_range)

        # 刷新画布
        self.plot_widget.draw()

    def circle_from_polar(self, p1, p2, p3):
        """
        从三个极坐标点计算拟合圆参数
        对应MATLAB中的circle_from_polar函数

        Args:
            p1, p2, p3: 极坐标点 [r, theta]

        Returns:
            xc, yc: 圆心坐标
            D: 圆的直径
        """
        # 极坐标转直角坐标
        x1 = p1[0] * np.cos(p1[1])
        y1 = p1[0] * np.sin(p1[1])
        x2 = p2[0] * np.cos(p2[1])
        y2 = p2[0] * np.sin(p2[1])
        x3 = p3[0] * np.cos(p3[1])
        y3 = p3[0] * np.sin(p3[1])

        # 计算分母
        D_denom = 2 * (x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))

        if abs(D_denom) < 1e-10:
            raise ValueError('三点共线，无法拟合圆')

        # 计算中间变量
        x1s = x1**2 + y1**2
        x2s = x2**2 + y2**2
        x3s = x3**2 + y3**2

        # 计算圆心坐标
        xc = (x1s*(y2 - y3) + x2s*(y3 - y1) + x3s*(y1 - y2)) / D_denom
        yc = (x1s*(x3 - x2) + x2s*(x1 - x3) + x3s*(x2 - x1)) / D_denom

        # 计算半径和直径
        R = np.sqrt((x1 - xc)**2 + (y1 - yc)**2)
        D = 2 * R

        return xc, yc, D

    def plot_fitted_circle_1(self, result):
        """绘制拟合圆图1 (左上角) - 在UI界面坐标图上绘制拟合圆"""
        ax = self.plot_widget.ax1
        ax.clear()

        # 获取拟合圆参数
        xc, yc = result['center_x'], result['center_y']
        radius = result['radius']
        measure_points = result['measure_points']

        # 绘制拟合圆
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = xc + radius * np.cos(theta)
        y_circle = yc + radius * np.sin(theta)
        ax.plot(x_circle, y_circle, 'r-', linewidth=2)

        # 绘制测量点
        x_measured = []
        y_measured = []
        for point in measure_points:
            r, theta_val = point
            x = r * np.cos(theta_val)
            y = r * np.sin(theta_val)
            x_measured.append(x)
            y_measured.append(y)

        ax.scatter(x_measured, y_measured, c='blue', s=80, alpha=0.8, zorder=5)

        # 绘制拟合圆心
        ax.plot(xc, yc, 'ro', markersize=8, zorder=5)

        # 设置图例 - 只显示拟合圆心坐标
        ax.legend([f'拟合圆心: ({xc:.3f}, {yc:.3f})'], loc='upper right', fontsize=9)

        # 设置图表属性
        ax.set_xlabel('X (mm)', fontsize=9)
        ax.set_ylabel('Y (mm)', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # 刷新画布
        self.plot_widget.draw()

    def plot_fitted_circle_2(self, result):
        """绘制拟合圆图2 (右上角) - 在UI界面坐标图上绘制拟合圆"""
        ax = self.plot_widget.ax2
        ax.clear()

        # 获取拟合圆参数
        xc, yc = result['center_x'], result['center_y']
        radius = result['radius']

        # 绘制拟合圆
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = xc + radius * np.cos(theta)
        y_circle = yc + radius * np.sin(theta)
        ax.plot(x_circle, y_circle, 'r-', linewidth=2)

        # 绘制拟合圆心
        ax.plot(xc, yc, 'ro', markersize=8, zorder=5)

        # 设置图例 - 只显示拟合圆心坐标
        ax.legend([f'拟合圆心: ({xc:.3f}, {yc:.3f})'], loc='upper right', fontsize=9)

        # 设置图表属性
        ax.set_xlabel('X (mm)', fontsize=9)
        ax.set_ylabel('Y (mm)', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # 刷新画布
        self.plot_widget.draw()

    def plot_fitted_circle_3(self, result):
        """绘制拟合圆图3 (左下角) - 在UI界面坐标图上绘制拟合圆"""
        ax = self.plot_widget.ax3
        ax.clear()

        # 获取拟合圆参数
        xc, yc = result['center_x'], result['center_y']
        radius = result['radius']
        measure_points = result['measure_points']

        # 绘制拟合圆
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = xc + radius * np.cos(theta)
        y_circle = yc + radius * np.sin(theta)
        ax.plot(x_circle, y_circle, 'r-', linewidth=2)

        # 绘制测量点
        for point in measure_points:
            r, theta_val = point
            x = r * np.cos(theta_val)
            y = r * np.sin(theta_val)
            ax.scatter(x, y, c='blue', s=80, alpha=0.8, zorder=5)

        # 绘制拟合圆心
        ax.plot(xc, yc, 'ro', markersize=8, zorder=5)

        # 设置图例 - 只显示拟合圆心坐标
        ax.legend([f'拟合圆心: ({xc:.3f}, {yc:.3f})'], loc='upper right', fontsize=9)

        # 设置图表属性
        ax.set_xlabel('X (mm)', fontsize=9)
        ax.set_ylabel('Y (mm)', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # 刷新画布
        self.plot_widget.draw()

    def plot_fitted_circle_4(self, result):
        """绘制拟合圆图4 (右下角) - 在UI界面坐标图上绘制拟合圆"""
        ax = self.plot_widget.ax4
        ax.clear()

        # 获取拟合圆参数
        xc, yc = result['center_x'], result['center_y']
        radius = result['radius']
        measure_points = result['measure_points']

        # 绘制拟合圆
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = xc + radius * np.cos(theta)
        y_circle = yc + radius * np.sin(theta)
        ax.plot(x_circle, y_circle, 'r-', linewidth=2)

        # 绘制测量点
        for point in measure_points:
            r, theta_val = point
            x = r * np.cos(theta_val)
            y = r * np.sin(theta_val)
            ax.scatter(x, y, c='blue', s=80, alpha=0.8, zorder=5)

        # 绘制拟合圆心
        ax.plot(xc, yc, 'ro', markersize=8, zorder=5)

        # 设置图例 - 只显示拟合圆心坐标
        ax.legend([f'拟合圆心: ({xc:.3f}, {yc:.3f})'], loc='upper right', fontsize=9)

        # 设置图表属性
        ax.set_xlabel('X (mm)', fontsize=9)
        ax.set_ylabel('Y (mm)', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # 刷新画布
        self.plot_widget.draw()







if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 初始化数据库并创建示例数据
    db_manager.create_sample_data()
    
    # 添加一些测试数据
    import numpy as np
    for i in range(50):
        depth = i * 2.0
        diameter = 25.0 + 0.1 * np.sin(depth * 0.1) + np.random.normal(0, 0.02)
        db_manager.add_measurement_data("H001", depth, diameter)
    
    # 创建历史数据查看器
    viewer = HistoryViewer()
    viewer.show()
    
    sys.exit(app.exec())
