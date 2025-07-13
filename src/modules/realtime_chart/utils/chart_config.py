"""图表配置模块"""

class ChartConfig:
    """图表配置常量"""
    
    # 数据缓冲区大小
    BUFFER_SIZE = 1000
    MIN_DISPLAY_POINTS = 50
    
    # 标准直径配置
    DEFAULT_STANDARD_DIAMETER = 17.6  # mm
    DEFAULT_TOLERANCE = 0.2  # mm
    
    # 图表样式
    FIGURE_BGCOLOR = '#f0f0f0'
    AXES_BGCOLOR = '#ffffff'
    
    # 线条样式
    LINE_COLOR = '#1976D2'
    LINE_WIDTH = 2.0
    
    # 误差线样式
    ERROR_LINE_COLOR = '#FF5722'
    ERROR_LINE_WIDTH = 2.0
    ERROR_LINE_STYLE = '--'
    
    # 公差区域样式
    TOLERANCE_FILL_COLOR = '#4CAF50'
    TOLERANCE_FILL_ALPHA = 0.15
    
    # Y轴范围
    Y_AXIS_PADDING = 0.5  # mm
    Y_AXIS_FOCUS_PADDING = 0.3  # mm
    Y_AXIS_DEFAULT_RANGE = (10.0, 25.0)  # mm
    
    # 异常检测
    ANOMALY_THRESHOLD_RATIO = 1.0  # 相对于公差的倍数
    
    # 动画更新间隔
    UPDATE_INTERVAL = 100  # ms
    
    # CSV导入配置
    CSV_UPDATE_INTERVAL = 50  # ms
    CSV_POINTS_PER_UPDATE = 1
    
    # 内窥镜图像切换
    ENDOSCOPE_IMAGE_SWITCH_INTERVAL = 5  # seconds