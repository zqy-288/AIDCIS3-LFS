# AIDCIS3-LFS 使用示例

![Examples](https://img.shields.io/badge/examples-comprehensive-brightgreen)
![MVVM](https://img.shields.io/badge/pattern-MVVM-blue)
![Best Practices](https://img.shields.io/badge/practices-best-orange)

> 📚 **完整的使用示例集合** - 从基础用法到高级扩展的实战代码

## 📋 示例概览

本目录包含AIDCIS3-LFS系统的完整使用示例，涵盖从基础应用启动到高级功能扩展的各种场景。所有示例都基于MVVM架构设计，展示了最佳实践和推荐模式。

## 🗂️ 示例结构

```
docs/examples/
├── README.md                          # 本文件
├── basic_usage/                       # 基础使用示例
│   ├── simple_startup.py             # 简单应用启动
│   ├── file_loading.py               # 文件加载示例
│   └── basic_detection.py            # 基础检测流程
├── advanced_usage/                    # 高级使用示例
│   ├── custom_services.py            # 自定义服务
│   ├── plugin_development.py         # 插件开发
│   └── performance_optimization.py   # 性能优化
├── integration_examples/              # 集成示例
│   ├── database_integration.py       # 数据库集成
│   ├── external_api_integration.py   # 外部API集成
│   └── batch_processing.py           # 批量处理
├── testing_examples/                  # 测试示例
│   ├── unit_test_examples.py         # 单元测试
│   ├── integration_test_examples.py  # 集成测试
│   └── mock_examples.py              # Mock使用
├── ui_customization/                  # UI定制示例
│   ├── custom_components.py          # 自定义组件
│   ├── theme_customization.py        # 主题定制
│   └── layout_examples.py            # 布局示例
└── deployment/                       # 部署示例
    ├── docker_deployment/            # Docker部署
    ├── standalone_executable/        # 独立可执行文件
    └── configuration_examples/       # 配置示例
```

## 🚀 快速开始示例

### 最简启动

```python
#!/usr/bin/env python3
"""最简单的应用启动示例"""

import sys
from PySide6.QtWidgets import QApplication
from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator

def main():
    app = QApplication(sys.argv)
    coordinator = MainWindowCoordinator()
    coordinator.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

### 带日志的启动

```python
#!/usr/bin/env python3
"""带完整日志配置的启动示例"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/application.log'),
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("AIDCIS3-LFS")
        app.setApplicationVersion("2.0.0")
        
        coordinator = MainWindowCoordinator()
        coordinator.show()
        
        logger.info("应用启动成功")
        return app.exec()
    
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## 📊 使用场景分类

### 🎯 基础使用 (basic_usage/)
适合初学者和基本需求的示例：
- 应用启动和关闭
- 文件加载和保存
- 基础检测流程
- UI基本操作

### 🚀 高级使用 (advanced_usage/)
适合有经验的开发者：
- 自定义服务实现
- 插件开发
- 性能优化技巧
- 高级配置

### 🔗 集成示例 (integration_examples/)
系统集成相关示例：
- 数据库连接和操作
- 外部API调用
- 批量数据处理
- 第三方库集成

### 🧪 测试示例 (testing_examples/)
测试相关的最佳实践：
- 单元测试编写
- 集成测试设计
- Mock对象使用
- 性能测试

### 🎨 UI定制 (ui_customization/)
界面定制和扩展：
- 自定义UI组件
- 主题和样式
- 布局管理
- 交互设计

### 📦 部署示例 (deployment/)
部署和分发相关：
- Docker容器化
- 独立可执行文件
- 配置管理
- 环境部署

## 💡 最佳实践提示

### 1. 代码组织
```python
# 推荐的导入顺序
# 1. 标准库
import sys
import logging
from typing import Dict, Any

# 2. 第三方库
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal

# 3. 本地模块
from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator
from src.ui.view_models.main_view_model import MainViewModel
```

### 2. 错误处理
```python
# 推荐的错误处理模式
try:
    coordinator = MainWindowCoordinator()
    coordinator.show()
except ImportError as e:
    logger.error(f"模块导入失败: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"未知错误: {e}")
    sys.exit(1)
```

### 3. 资源管理
```python
# 推荐的资源清理模式
def cleanup_resources():
    """清理应用资源"""
    try:
        coordinator.close()
        logger.info("应用资源已清理")
    except Exception as e:
        logger.error(f"资源清理失败: {e}")

# 注册清理函数
import atexit
atexit.register(cleanup_resources)
```

## 🔧 开发环境设置

### 1. 依赖安装
```bash
# 安装基础依赖
pip install -r config/requirements.txt

# 安装测试依赖
python test_runner_with_coverage.py install

# 安装开发依赖（可选）
pip install black flake8 mypy
```

### 2. 环境变量
```bash
# 设置调试模式
export AIDCIS_DEBUG=1

# 设置日志级别
export AIDCIS_LOG_LEVEL=DEBUG

# 设置数据目录
export AIDCIS_DATA_DIR=/path/to/data
```

### 3. 开发工具配置
```python
# .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true
}
```

## 📖 示例使用指南

### 运行示例
```bash
# 运行基础示例
cd docs/examples/basic_usage
python simple_startup.py

# 运行高级示例
cd docs/examples/advanced_usage
python custom_services.py

# 运行测试示例
cd docs/examples/testing_examples
python -m pytest unit_test_examples.py -v
```

### 修改示例
1. 复制示例文件到你的项目目录
2. 根据需要修改配置和参数
3. 运行并测试修改后的代码
4. 参考注释理解实现原理

### 故障排除
```python
# 常见问题检查清单
def check_environment():
    """检查运行环境"""
    import sys
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("需要Python 3.8或更高版本")
        return False
    
    # 检查依赖
    try:
        import PySide6
        print(f"PySide6版本: {PySide6.__version__}")
    except ImportError:
        print("PySide6未安装")
        return False
    
    # 检查项目路径
    try:
        from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator
        print("项目模块导入成功")
    except ImportError as e:
        print(f"项目模块导入失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if check_environment():
        print("✅ 环境检查通过")
    else:
        print("❌ 环境检查失败")
```

## 🤝 贡献新示例

### 示例规范
1. **文件命名**: 使用描述性的名称，如 `custom_detection_service.py`
2. **文档字符串**: 每个示例文件开头包含完整的说明
3. **注释**: 关键代码段添加详细注释
4. **错误处理**: 包含适当的错误处理逻辑
5. **测试**: 如果可能，包含简单的测试验证

### 示例模板
```python
#!/usr/bin/env python3
"""
示例名称: [简短描述]

功能描述:
- 功能点1
- 功能点2
- 功能点3

使用方法:
python example_file.py

依赖要求:
- PySide6 >= 6.0.0
- 其他依赖...

作者: [作者名]
创建时间: [日期]
"""

import sys
import logging
from typing import Dict, Any

# 主要实现代码
def main():
    """主函数"""
    pass

# 辅助函数
def helper_function():
    """辅助函数说明"""
    pass

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\\n用户中断执行")
        sys.exit(0)
    except Exception as e:
        logging.error(f"执行失败: {e}")
        sys.exit(1)
```

## 📚 相关文档

- [README.md](../../README.md) - 项目总览
- [API_REFERENCE.md](../../API_REFERENCE.md) - API参考
- [MIGRATION_GUIDE.md](../../MIGRATION_GUIDE.md) - 迁移指南
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - 架构设计

## 📞 获取帮助

如果在使用示例过程中遇到问题：

1. 查看对应示例的文档字符串和注释
2. 检查[故障排除](#故障排除)部分
3. 查阅相关的API文档
4. 在项目Issues中搜索类似问题
5. 提交新的Issue寻求帮助

---

**🎯 目标**: 帮助开发者快速掌握AIDCIS3-LFS的使用方法

**📈 完成度**: 示例覆盖率 > 90%的常用场景

**📅 更新**: 随项目版本同步更新

**🔄 版本**: v2.0.0 示例文档

**📅 最后更新**: 2025-07-25