"""
AIDCIS3-LFS Version Management
版本控制模块 - 管理软件版本信息
"""

__version__ = "2.0.0"
__version_info__ = (2, 0, 0)

# 版本元数据
VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_BUILD = "20250718"

# 项目信息
PROJECT_NAME = "AIDCIS3-LFS"
PROJECT_FULL_NAME = "AI-Driven Coordinated Inspection System - Large File Support"
PROJECT_DESCRIPTION = "管孔检测系统 - 支持大文件和插件化架构"

# 构建信息
BUILD_DATE = "2025-07-18"
BUILD_TYPE = "Release"
ARCHITECTURE = "Plugin-Based Modular Architecture"

# 功能版本标识
PLUGIN_SYSTEM_VERSION = "1.0.0"
UI_FRAMEWORK_VERSION = "PySide6"
DATABASE_VERSION = "SQLite 3"

def get_version():
    """获取完整版本字符串"""
    return __version__

def get_version_info():
    """获取版本信息元组"""
    return __version_info__

def get_build_info():
    """获取构建信息"""
    return {
        "version": __version__,
        "build_date": BUILD_DATE,
        "build_type": BUILD_TYPE,
        "architecture": ARCHITECTURE,
        "project_name": PROJECT_NAME,
        "plugin_system": PLUGIN_SYSTEM_VERSION
    }

def get_full_version_string():
    """获取完整版本描述"""
    return f"{PROJECT_NAME} v{__version__} ({BUILD_DATE})"

def print_version_info():
    """打印版本信息"""
    print("=" * 60)
    print(f"项目名称: {PROJECT_FULL_NAME}")
    print(f"版本: {__version__}")
    print(f"构建日期: {BUILD_DATE}")
    print(f"构建类型: {BUILD_TYPE}")
    print(f"架构: {ARCHITECTURE}")
    print(f"插件系统版本: {PLUGIN_SYSTEM_VERSION}")
    print(f"UI框架: {UI_FRAMEWORK_VERSION}")
    print(f"数据库: {DATABASE_VERSION}")
    print("=" * 60)

# 版本兼容性检查
MINIMUM_PYTHON_VERSION = (3, 8)
SUPPORTED_PLATFORMS = ["Windows", "Linux", "macOS"]

def check_python_version():
    """检查Python版本兼容性"""
    import sys
    current_version = sys.version_info[:2]
    if current_version < MINIMUM_PYTHON_VERSION:
        raise RuntimeError(
            f"Python {MINIMUM_PYTHON_VERSION[0]}.{MINIMUM_PYTHON_VERSION[1]}+ is required. "
            f"You are using Python {current_version[0]}.{current_version[1]}"
        )
    return True

# 更新日志条目
CHANGELOG = {
    "2.0.0": [
        "完成插件化架构设计 - 企业级插件系统",
        "实现全局错误处理机制 - 统一错误管理",
        "完成依赖注入框架 - 模块化依赖管理", 
        "实现UI组件生命周期管理",
        "完成数据访问层抽象和Repository模式",
        "添加配置管理系统和热重载",
        "实现应用程序核心架构重构",
        "添加性能监控和基准测试",
        "完成主窗口适配器模式重构",
        "升级项目版本控制系统到2.0.0",
        "统一启动入口 - 唯一启动方式run_project.py",
        "重命名核心模块 - aidcis2 → core_business"
    ],
    "1.0.0": [
        "项目结构重组和优化",
        "Git LFS配置和大文件管理", 
        "实时监控界面优化",
        "完整的文档和工具集",
        "团队协作流程建立"
    ]
}

def get_changelog(version=None):
    """获取更新日志"""
    if version:
        return CHANGELOG.get(version, [])
    return CHANGELOG