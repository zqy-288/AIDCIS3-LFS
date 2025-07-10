"""
检测报告系统测试框架
包含单元测试、系统测试和端到端测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 测试配置
TEST_CONFIG = {
    'temp_dir': project_root / "tests" / "temp",
    'test_data_dir': project_root / "tests" / "test_data", 
    'output_dir': project_root / "tests" / "output",
    'timeout': 30,  # 测试超时时间（秒）
}

# 确保测试目录存在
for dir_path in TEST_CONFIG.values():
    if isinstance(dir_path, Path):
        dir_path.mkdir(exist_ok=True, parents=True)