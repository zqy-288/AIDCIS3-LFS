"""
向后兼容导入代理
该包已迁移到 src.modules.panorama_view
"""
import warnings

warnings.warn(
    "src.core_business.graphics.panorama 已迁移到 src.modules.panorama_view，"
    "请更新您的导入路径。此兼容层将在未来版本中移除。",
    DeprecationWarning,
    stacklevel=2
)

# 代理导入 - 从新位置导入所有内容
from src.modules.panorama_view import *