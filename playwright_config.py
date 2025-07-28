"""
Playwright测试配置模块
Configuration module for Playwright testing
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class TestEnvironment:
    """测试环境配置"""
    name: str = "test"
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    slow_mo: int = 0
    video: bool = False
    screenshot: str = "only-on-failure"

@dataclass
class RetryConfig:
    """重试配置"""
    max_failures: int = 3
    retries: int = 2
    timeout: int = 60000

@dataclass
class PerformanceConfig:
    """性能测试配置"""
    memory_threshold_mb: int = 1000
    startup_time_threshold_s: float = 10.0
    response_time_threshold_ms: int = 5000
    
# 默认配置
CONFIG = TestEnvironment(
    name="AIDCIS3-LFS-UI-Tests",
    headless=True,
    viewport_width=1920,
    viewport_height=1080,
    timeout=30000,
    slow_mo=0,
    video=False,
    screenshot="only-on-failure"
)

RETRY_CONFIG = RetryConfig(
    max_failures=3,
    retries=2,
    timeout=60000
)

PERFORMANCE_CONFIG = PerformanceConfig(
    memory_threshold_mb=1000,
    startup_time_threshold_s=10.0,
    response_time_threshold_ms=5000
)

# 浏览器配置
BROWSER_CONFIG = {
    "channel": "chrome",
    "headless": True,
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor"
    ]
}

# 测试数据配置
TEST_DATA_CONFIG = {
    "test_files": {
        "dxf": "assets/dxf/DXF Graph/测试管板.dxf",
        "product": "CAP1000"
    },
    "screenshots_dir": "tests/screenshots",
    "reports_dir": "reports/test_reports"
}

def get_config_for_environment(env: str = "test") -> TestEnvironment:
    """根据环境获取配置"""
    if env == "ci":
        return TestEnvironment(
            name="CI-Tests",
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            timeout=60000,
            slow_mo=0,
            video=True,
            screenshot="only-on-failure"
        )
    elif env == "debug":
        return TestEnvironment(
            name="Debug-Tests",
            headless=False,
            viewport_width=1920,
            viewport_height=1080,
            timeout=120000,
            slow_mo=1000,
            video=True,
            screenshot="on"
        )
    else:
        return CONFIG

def get_test_data_path(file_type: str) -> Optional[str]:
    """获取测试数据文件路径"""
    return TEST_DATA_CONFIG["test_files"].get(file_type)