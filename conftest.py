"""
Simplified conftest for zero tolerance testing
"""

import pytest
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def qt_app():
    """Qt应用程序fixture"""
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
        app.setApplicationName("AIDCIS3-LFS-Test")
        app.setQuitOnLastWindowClosed(False)
    else:
        app = QApplication.instance()
    
    yield app
    
    # Clean up
    app.processEvents()

# 自定义标记
def pytest_configure(config):
    """配置自定义标记"""
    config.addinivalue_line("markers", "ui: UI related tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")