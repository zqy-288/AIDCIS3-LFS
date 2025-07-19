# AIDCIS3-LFS 管孔检测系统

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 🎯 项目简介

AIDCIS3-LFS（AI Detection and Classification Inspection System - Large Format Support）是一个基于人工智能的大型工件管孔检测系统。该系统采用现代化的ApplicationCore架构，提供实时检测、可视化分析和智能报告生成功能。

### 主要特性

- 🔍 **智能检测**：基于AI算法的管孔检测和分类
- 📊 **实时监控**：实时图表和状态监控
- 🎨 **现代UI**：深蓝色主题的专业界面
- 🏗️ **企业架构**：ApplicationCore + 依赖注入 + 事件驱动
- 🔌 **插件系统**：可扩展的插件架构
- 📋 **报告生成**：自动化的检测报告和数据导出
- 🗃️ **数据管理**：SQLite数据库存储和历史数据查看

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- PySide6 6.0+
- SQLite 3.x
- 推荐操作系统：Windows 10/11, macOS 10.15+, Ubuntu 20.04+

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/AIDCIS3-LFS.git
cd AIDCIS3-LFS
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用程序**
```bash
python3 run_project.py
```

### 首次运行

应用程序首次启动时会自动：
- 创建数据库文件 `detection_system.db`
- 初始化默认配置
- 应用深蓝色主题
- 创建必要的日志目录

## 🏗️ 项目架构

### 核心架构

```
AIDCIS3-LFS/
├── run_project.py              # 主启动脚本
├── src/                        # 源代码目录
│   ├── main_window.py          # 主窗口模块
│   ├── core/                   # 核心架构
│   │   ├── application.py      # ApplicationCore
│   │   ├── dependency_injection.py  # 依赖注入
│   │   ├── error_recovery.py   # 错误恢复
│   │   └── interfaces/         # 接口定义
│   ├── core_business/          # 业务逻辑
│   │   ├── models/             # 数据模型
│   │   ├── graphics/           # 图形组件
│   │   └── data_adapter.py     # 数据适配器
│   ├── modules/                # 功能模块
│   │   ├── theme_manager_unified.py  # 主题管理
│   │   ├── realtime_chart.py   # 实时图表
│   │   └── worker_thread.py    # 工作线程
│   └── data/                   # 数据访问层
├── config/                     # 配置文件
├── Data/                       # 数据目录
├── assets/                     # 资源文件
└── logs/                       # 日志文件
```

### ApplicationCore架构

本项目采用现代化的ApplicationCore架构，包含：

- **依赖注入容器**：统一的组件管理
- **事件驱动系统**：松耦合的组件通信
- **插件系统**：可扩展的功能模块
- **错误恢复机制**：自动化的错误处理
- **生命周期管理**：统一的组件生命周期

## 🎨 主题系统

### 深蓝色主题

系统采用专业的深蓝色主题配色：

- **主背景色**：`#2C313C` (深色)
- **面板背景色**：`#313642` (深灰)
- **主题蓝色**：`#007ACC` (深蓝)
- **主文本色**：`#D3D8E0` (浅色)
- **成功色**：`#2ECC71` (绿色)
- **警告色**：`#E67E22` (橙色)
- **错误色**：`#E74C3C` (红色)

### 主题管理

系统使用统一的主题管理器：
- 自动应用深色主题
- 支持主题一致性检查
- 提供主题协调器管理

## 📊 功能模块

### 检测功能

- **实时检测**：支持实时管孔检测和分类
- **批量处理**：支持多文件批量检测
- **结果可视化**：直观的检测结果展示
- **数据导出**：支持多种格式的数据导出

### 数据管理

- **SQLite数据库**：本地数据存储
- **历史记录**：完整的检测历史查看
- **数据分析**：统计分析和趋势展示
- **报告生成**：自动化的检测报告

### 用户界面

- **主检测视图**：核心检测界面
- **实时监控面板**：系统状态监控
- **历史数据查看器**：历史数据浏览
- **设置面板**：系统配置管理

## 🔧 开发指南

### 开发环境设置

1. **克隆项目**
```bash
git clone https://github.com/yourusername/AIDCIS3-LFS.git
cd AIDCIS3-LFS
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装开发依赖**
```bash
pip install -r requirements-dev.txt
```

### 代码结构

- **核心模块**：`src/core/` - ApplicationCore架构
- **业务逻辑**：`src/core_business/` - 检测业务逻辑
- **UI组件**：`src/modules/` - 界面组件
- **数据层**：`src/data/` - 数据访问层

### 依赖注入

使用装饰器注册服务：
```python
from src.core.dependency_injection import injectable, ServiceLifetime

@injectable(ServiceLifetime.SINGLETON)
class MyService:
    def __init__(self):
        pass
```

### 事件系统

使用事件总线进行组件通信：
```python
from src.core.application import ApplicationEvent

# 发布事件
event = ApplicationEvent("detection_completed", {"result": result})
app.event_bus.publish(event)

# 订阅事件
app.event_bus.subscribe("detection_completed", self.on_detection_completed)
```

## 📋 配置说明

### 主配置文件

`config/config.json`：
```json
{
  "app_name": "AIDCIS3-LFS",
  "version": "2.0.0",
  "database": {
    "url": "sqlite:///detection_system.db",
    "echo": false
  },
  "ui": {
    "theme": "dark",
    "font_size": 15,
    "window_size": [1400, 900]
  },
  "detection": {
    "confidence_threshold": 0.6,
    "batch_size": 32
  }
}
```

### 数据库配置

系统使用SQLite数据库存储：
- **数据库文件**：`detection_system.db`
- **表结构**：自动创建和维护
- **数据迁移**：自动处理版本升级

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_core.py

# 生成覆盖率报告
python -m pytest --cov=src tests/
```

### 测试覆盖范围

- 核心架构测试
- 业务逻辑测试
- UI组件测试
- 数据层测试
- 集成测试

## 📝 日志系统

### 日志配置

- **日志目录**：`logs/`
- **日志级别**：INFO, WARNING, ERROR
- **日志格式**：时间戳 + 模块名 + 级别 + 消息
- **日志轮转**：按日期和大小自动轮转

### 日志查看

```bash
# 查看应用日志
tail -f logs/application.log

# 查看错误日志
tail -f logs/error.log
```

## 🔌 插件开发

### 插件接口

```python
from src.core.interfaces.plugin_interfaces import IPlugin

class MyPlugin(IPlugin):
    def initialize(self) -> bool:
        pass
    
    def execute(self, context: dict) -> dict:
        pass
    
    def cleanup(self) -> None:
        pass
```

### 插件注册

```python
from src.core.plugin_manager import PluginManager

plugin_manager = PluginManager()
plugin_manager.register_plugin("my_plugin", MyPlugin())
```

## 🚨 故障排除

### 常见问题

1. **应用程序启动失败**
   - 检查Python版本（需要3.8+）
   - 确认依赖包已安装
   - 查看日志文件错误信息

2. **数据库连接失败**
   - 检查数据库文件权限
   - 确认SQLite版本兼容性
   - 查看数据库连接配置

3. **主题显示异常**
   - 检查主题文件是否完整
   - 确认Qt版本兼容性
   - 重启应用程序

### 调试模式

启用调试模式：
```bash
python run_project.py --debug
```

## 📚 API文档

### 核心API

- **ApplicationCore**：应用程序核心管理
- **DependencyContainer**：依赖注入容器
- **EventBus**：事件总线
- **PluginManager**：插件管理器

### 业务API

- **DetectionEngine**：检测引擎
- **DataAdapter**：数据适配器
- **ReportGenerator**：报告生成器

完整的API文档请参考 `docs/api.md`。

## 🤝 贡献指南

### 贡献流程

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 使用 PEP 8 代码风格
- 添加适当的注释和文档字符串
- 编写单元测试
- 遵循现有的架构模式

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参考 [LICENSE](LICENSE) 文件。

## 📞 支持与联系

- **项目主页**：https://github.com/yourusername/AIDCIS3-LFS
- **问题反馈**：https://github.com/yourusername/AIDCIS3-LFS/issues
- **邮箱**：your.email@example.com

## 🎉 致谢

感谢所有为本项目做出贡献的开发者和用户！

---

**版本**：2.0.0  
**最后更新**：2025年1月18日  
**维护状态**：活跃开发中 🚀