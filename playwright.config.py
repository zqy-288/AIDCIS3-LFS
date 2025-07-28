"""
Playwright Configuration for AIDCIS3-LFS UI Testing
零容忍测试配置 - 高质量自动化测试
"""

from playwright.sync_api import Playwright
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 测试配置
CONFIG = {
    # 基础配置
    'headless': False,  # 显示浏览器以便调试
    'slow_mo': 100,     # 操作间延迟100ms便于观察
    'timeout': 30000,   # 30秒超时
    'action_timeout': 10000,  # 操作超时10秒
    
    # 浏览器配置
    'browsers': ['chromium'],  # 使用Chromium进行测试
    'viewport': {'width': 1920, 'height': 1080},
    
    # 截图和录像
    'screenshot_on_failure': True,
    'video_on_failure': True,
    'trace_on_failure': True,
    
    # 测试数据
    'test_data_dir': PROJECT_ROOT / 'tests' / 'test_data',
    'output_dir': PROJECT_ROOT / 'tests' / 'output',
    'reports_dir': PROJECT_ROOT / 'tests' / 'reports',
    
    # 应用程序配置
    'app_port': 8080,
    'app_host': 'localhost',
    'app_startup_timeout': 30000,
}

# Playwright测试配置
def pytest_configure(config):
    """Pytest配置hook"""
    # 创建输出目录
    for dir_path in [CONFIG['output_dir'], CONFIG['reports_dir'], CONFIG['test_data_dir']]:
        dir_path.mkdir(parents=True, exist_ok=True)

def browser_context_args():
    """浏览器上下文参数"""
    return {
        'viewport': CONFIG['viewport'],
        'record_video_dir': CONFIG['output_dir'] / 'videos',
        'record_video_size': CONFIG['viewport'],
    }

def browser_type_launch_args():
    """浏览器启动参数"""
    return {
        'headless': CONFIG['headless'],
        'slow_mo': CONFIG['slow_mo'],
        'timeout': CONFIG['timeout'],
        'args': [
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--allow-running-insecure-content',
            '--disable-blink-features=AutomationControlled'
        ]
    }

# PySide6应用程序测试配置
PYSIDE6_CONFIG = {
    'app_module': 'src.main_window',
    'app_class': 'MainWindow',
    'startup_args': [],
    'cleanup_timeout': 5000,
    'screenshot_format': 'PNG',
    'test_modes': ['unit', 'integration', 'e2e'],
}

class TestEnvironment:
    """测试环境管理器"""
    
    def __init__(self):
        self.app = None
        self.browser = None
        self.context = None
        self.page = None
        
    def setup_app(self):
        """设置PySide6应用程序"""
        import sys
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        # 创建应用程序实例
        if not QApplication.instance():
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
            
        # 设置应用程序属性
        self.app.setApplicationName("AIDCIS3-LFS")
        self.app.setApplicationVersion("4.0")
        
        return self.app
        
    def setup_browser(self, playwright: Playwright):
        """设置浏览器环境"""
        self.browser = playwright.chromium.launch(**browser_type_launch_args())
        self.context = self.browser.new_context(**browser_context_args())
        self.page = self.context.new_page()
        
        # 设置页面超时
        self.page.set_default_timeout(CONFIG['timeout'])
        self.page.set_default_navigation_timeout(CONFIG['timeout'])
        
        return self.page
        
    def cleanup(self):
        """清理测试环境"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.app:
            self.app.quit()

# 错误处理和重试配置
RETRY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 1000,  # 1秒
    'flaky_test_threshold': 0.1,  # 10%失败率认为是不稳定测试
}

# 性能测试配置
PERFORMANCE_CONFIG = {
    'memory_limit_mb': 1024,  # 1GB内存限制
    'cpu_usage_limit': 80,    # 80% CPU使用率限制
    'response_time_limit_ms': 5000,  # 5秒响应时间限制
    'fps_limit': 30,          # 30fps最小帧率
}

# 数据驱动测试配置
TEST_DATA_CONFIG = {
    'dxf_files': [
        'test_data.dxf',
        '测试管板.dxf',
        '东重管板.dxf'
    ],
    'hole_counts': [100, 500, 1000, 5000],
    'test_scenarios': [
        'basic_loading',
        'large_dataset',
        'error_handling',
        'performance_stress'
    ]
}

# 报告配置
REPORTING_CONFIG = {
    'formats': ['html', 'json', 'junit', 'allure'],
    'include_screenshots': True,
    'include_videos': True,
    'include_traces': True,
    'detailed_timing': True,
    'coverage_threshold': 90,  # 90%代码覆盖率要求
}