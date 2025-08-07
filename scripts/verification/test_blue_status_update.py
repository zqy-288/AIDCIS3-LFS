#!/usr/bin/env python3
"""
测试蓝色状态更新问题
"""

import sys
import os
import logging

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication
from src.pages.main_detection_p1.main_detection_page import MainDetectionPage

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建主检测页面
    page = MainDetectionPage()
    page.show()
    
    # 启动应用
    sys.exit(app.exec())

if __name__ == '__main__':
    main()