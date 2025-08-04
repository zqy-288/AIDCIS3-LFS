"""
常量定义
"""

# 图表设置
CHART_FIGURE_SIZE = (24, 12)
CHART_DPI = 100
CHART_UPDATE_INTERVAL = 100  # 毫秒

# 数据缓冲设置
MAX_DATA_POINTS = 1000
DATA_BUFFER_SIZE = 10000

# 异常检测设置
ANOMALY_THRESHOLD = 0.3  # mm
MAX_ANOMALIES_DISPLAY = 50

# CSV监控设置
CSV_CHECK_INTERVAL = 1000  # 毫秒
CSV_STABLE_THRESHOLD = 3  # 秒
CSV_ARCHIVE_FOLDER = "历史CSV数据"

# 内窥镜设置
ENDOSCOPE_SWITCH_INTERVAL = 500  # 毫秒
ENDOSCOPE_IMAGE_CACHE_SIZE = 10

# 进程监控设置
PROCESS_CHECK_INTERVAL = 1000  # 毫秒
PROCESS_TIMEOUT = 30  # 秒

# 标准直径设置
DEFAULT_STANDARD_DIAMETER = 17.6  # mm
DEFAULT_TOLERANCE = 0.2  # mm

# UI设置
STATUS_UPDATE_INTERVAL = 100  # 毫秒
BUTTON_MIN_WIDTH = 100
LABEL_MIN_WIDTH = 180

# 文件路径设置 - 已移除硬编码，改为基于产品的动态路径
# DATA_FOLDER, IMAGE_FOLDER, CSV_FOLDER 现在通过 DataPathManager 动态获取
# 示例用法：
# from src.models.data_path_manager import DataPathManager
# path_manager = DataPathManager()
# product_path = path_manager.get_product_path(product_name)
# image_folder = product_path / "内窥镜图片"

# 孔位映射设置
ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
COLUMNS = range(1, 13)  # 1-12

# 日志设置
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"