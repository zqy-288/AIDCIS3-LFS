"""
Pytest配置文件 - AIDCIS3-LFS零容忍测试框架
Global test fixtures and configuration
"""

import pytest
import sys
import os
import time
import logging
from pathlib import Path
from typing import Generator, Optional
from playwright.sync_api import Playwright, Browser, BrowserContext, Page
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright_config import CONFIG, TestEnvironment, RETRY_CONFIG, PERFORMANCE_CONFIG

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'tests' / 'output' / 'test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TestSession:
    """测试会话管理器"""
    
    def __init__(self):
        self.app: Optional[QApplication] = None
        self.main_window = None
        self.test_env = TestEnvironment()
        self.start_time = time.time()
        self.test_count = 0
        self.failed_count = 0
        
    def setup_qt_app(self):
        """设置Qt应用程序"""
        if QApplication.instance() is None:
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("AIDCIS3-LFS-Test")
            self.app.setQuitOnLastWindowClosed(False)
        else:
            self.app = QApplication.instance()
        
        # 设置测试环境变量
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # 无头模式
        
        return self.app
        
    def create_main_window(self):
        """创建主窗口实例"""
        try:
            from src.main_window import MainWindow
            self.main_window = MainWindow()
            return self.main_window
        except Exception as e:
            logger.error(f"Failed to create main window: {e}")
            raise
            
    def cleanup(self):
        """清理测试环境"""
        if self.main_window:
            self.main_window.close()
            self.main_window = None
            
        if self.app:
            self.app.processEvents()
            QTimer.singleShot(100, self.app.quit)
            self.app = None

# 全局测试会话
test_session = TestSession()

@pytest.fixture(scope="session")
def setup_test_environment():
    """设置测试环境 - 会话级别"""
    logger.info("🚀 Starting AIDCIS3-LFS test session...")
    
    # 创建输出目录
    output_dirs = [
        PROJECT_ROOT / 'tests' / 'output',
        PROJECT_ROOT / 'tests' / 'reports',
        PROJECT_ROOT / 'tests' / 'screenshots',
        PROJECT_ROOT / 'tests' / 'videos',
        PROJECT_ROOT / 'tests' / 'traces'
    ]
    
    for dir_path in output_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # 设置Qt应用程序
    test_session.setup_qt_app()
    
    yield test_session
    
    # 清理
    logger.info("🧹 Cleaning up test environment...")
    test_session.cleanup()
    
    # 报告测试会话统计
    duration = time.time() - test_session.start_time
    logger.info(f"📊 Test session completed in {duration:.2f}s")
    logger.info(f"📋 Total tests: {test_session.test_count}")
    logger.info(f"❌ Failed tests: {test_session.failed_count}")

@pytest.fixture(scope="function")
def qt_app(setup_test_environment):
    """Qt应用程序fixture"""
    return setup_test_environment.app

@pytest.fixture(scope="function")
def main_window(qt_app):
    """主窗口fixture"""
    window = test_session.create_main_window()
    yield window
    
    # 清理窗口
    if window:
        window.close()
        qt_app.processEvents()

@pytest.fixture(scope="session")
def playwright() -> Generator[Playwright, None, None]:
    """Playwright实例fixture"""
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="function")
def browser(playwright: Playwright) -> Generator[Browser, None, None]:
    """浏览器实例fixture"""
    browser = playwright.chromium.launch(
        headless=CONFIG.headless,
        slow_mo=CONFIG.slow_mo
    )
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """浏览器上下文fixture"""
    context = browser.new_context(
        viewport={'width': CONFIG.viewport_width, 'height': CONFIG.viewport_height},
        record_video_dir=str(PROJECT_ROOT / 'tests' / 'output' / 'videos')
    )
    yield context
    context.close()

@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """页面实例fixture"""
    page = context.new_page()
    page.set_default_timeout(CONFIG.timeout)
    yield page
    page.close()

@pytest.fixture(scope="function")
def test_data_dir():
    """测试数据目录fixture"""
    return PROJECT_ROOT / 'tests' / 'test_data'

@pytest.fixture(scope="function")
def dxf_test_files(test_data_dir):
    """DXF测试文件fixture"""
    dxf_files = [
        PROJECT_ROOT / 'test_data.dxf',
        PROJECT_ROOT / 'assets' / 'dxf' / 'DXF Graph' / '测试管板.dxf',
        PROJECT_ROOT / 'assets' / 'dxf' / 'DXF Graph' / '东重管板.dxf'
    ]
    
    # 验证文件存在
    existing_files = [f for f in dxf_files if f.exists()]
    
    if not existing_files:
        pytest.skip("No DXF test files found")
    
    return existing_files

@pytest.fixture(autouse=True)
def test_tracker(request):
    """测试跟踪器 - 自动收集测试统计"""
    test_session.test_count += 1
    
    start_time = time.time()
    logger.info(f"🧪 Starting test: {request.node.name}")
    
    yield
    
    duration = time.time() - start_time
    
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        test_session.failed_count += 1
        logger.error(f"❌ Test failed: {request.node.name} (duration: {duration:.3f}s)")
    else:
        logger.info(f"✅ Test passed: {request.node.name} (duration: {duration:.3f}s)")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """收集测试报告信息"""
    outcome = yield
    rep = outcome.get_result()
    
    # 保存报告到测试项目中，用于后续处理
    setattr(item, f"rep_{rep.when}", rep)

@pytest.fixture(scope="function")
def performance_monitor():
    """性能监控fixture"""
    import psutil
    import threading
    
    class PerformanceMonitor:
        def __init__(self):
            self.cpu_usage = []
            self.memory_usage = []
            self.monitoring = False
            self.monitor_thread = None
            
        def start(self):
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor)
            self.monitor_thread.start()
            
        def stop(self):
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
                
        def _monitor(self):
            while self.monitoring:
                self.cpu_usage.append(psutil.cpu_percent())
                self.memory_usage.append(psutil.virtual_memory().percent)
                time.sleep(0.1)
                
        def get_stats(self):
            return {
                'avg_cpu': sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0,
                'max_cpu': max(self.cpu_usage) if self.cpu_usage else 0,
                'avg_memory': sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
                'max_memory': max(self.memory_usage) if self.memory_usage else 0,
            }
    
    monitor = PerformanceMonitor()
    monitor.start()
    
    yield monitor
    
    monitor.stop()
    stats = monitor.get_stats()
    
    # 检查性能阈值
    if stats['max_cpu'] > 80.0:  # 80% CPU threshold
        logger.warning(f"⚠️ High CPU usage detected: {stats['max_cpu']:.1f}%")
    
    if stats['max_memory'] > PERFORMANCE_CONFIG.memory_threshold_mb:
        logger.warning(f"⚠️ High memory usage detected: {stats['max_memory']:.1f}MB")

@pytest.fixture(scope="function")
def screenshot_on_failure(request, qt_app):
    """失败时自动截图fixture"""
    yield
    
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        timestamp = int(time.time())
        screenshot_path = PROJECT_ROOT / 'tests' / 'screenshots' / f'failure_{request.node.name}_{timestamp}.png'
        
        try:
            # 尝试截图
            if hasattr(qt_app, 'primaryScreen'):
                screen = qt_app.primaryScreen()
                pixmap = screen.grabWindow(0)
                pixmap.save(str(screenshot_path))
                logger.info(f"📸 Failure screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")

# 自定义标记
def pytest_configure(config):
    """配置自定义标记"""
    config.addinivalue_line("markers", "ui: UI related tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "critical: Critical functionality tests")

# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 为慢速测试添加标记
        if "performance" in item.nodeid or "large_dataset" in item.nodeid:
            item.add_marker(pytest.mark.slow)
            
        # 为关键测试添加标记
        if "main_window" in item.nodeid or "dxf_loading" in item.nodeid:
            item.add_marker(pytest.mark.critical)

# 命令行选项
def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--run-slow", action="store_true", default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--performance-only", action="store_true", default=False,
        help="run only performance tests"
    )
    parser.addoption(
        "--critical-only", action="store_true", default=False,
        help="run only critical tests"
    )

def pytest_runtest_setup(item):
    """测试运行设置"""
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("need --run-slow option to run")
        
    if item.config.getoption("--performance-only") and "performance" not in item.keywords:
        pytest.skip("skipping non-performance test")
        
    if item.config.getoption("--critical-only") and "critical" not in item.keywords:
        pytest.skip("skipping non-critical test")