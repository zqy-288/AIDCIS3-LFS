# 上位机软件 - 管孔检测系统

**最后更新时间: 2025-07-07**

## 1. 项目概述

本项目是一个基于 PySide6 开发的桌面应用程序，旨在为工业管孔检测提供一套完整的解决方案。软件集成了实时数据监控、历史数据追溯、工件图像显示和缺陷标注等功能，旨在提高检测效率和数据管理的准确性。

该系统通过一个直观的图形用户界面，将复杂的数据采集和分析过程简化，方便操作人员使用。

## 2. 主要功能

*   **主检测视图**: 提供检测任务的整体视图，并作为导航到其他功能模块的入口。
*   **实时数据监控**:
    *   使用 `pyqtgraph` 实时绘制传感器采集的数据曲线。
    *   支持从 **CSV 文件** 导入数据进行模拟测量，方便调试和演示。
    *   显示当前测量的状态和基本信息。
*   **历史数据查看**:
    *   从 SQLite 数据库中检索历史检测数据。
    *   支持按工件或孔ID进行数据筛选和查看。
*   **缺陷标注工具**:
    *   加载工件的截面图或内窥镜图像。
    *   提供基本的绘图工具，允许用户在图像上标记和注释缺陷。
*   **数据持久化**:
    *   所有检测数据（包括工件信息、测量数据和点位坐标）均通过 `SQLAlchemy` ORM 框架存储在本地 `detection_system.db` (SQLite) 数据库中。

## 3. 技术栈

*   **核心框架**: Python 3.8+
*   **UI**: PySide6 >= 6.5.0
*   **图表**: pyqtgraph >= 0.13.0, Matplotlib >= 3.7.0
*   **数据处理与科学计算**: NumPy >= 1.24.0, SciPy >= 1.10.0
*   **数据库**: SQLAlchemy >= 2.0.0
*   **图像处理**: Pillow >= 9.0.0, OpenCV-Python >= 4.7.0

## 4. 安装与运行

### 4.1. 环境准备

确保你的系统已经安装了 Python 3.8 或更高版本。

### 4.2. 安装依赖

在项目根目录下，通过 `pip` 安装所有必要的依赖库：

```bash
pip install -r requirements.txt
```

### 4.3. 运行程序

依赖安装完成后，直接运行 `main.py` 即可启动应用程序：

```bash
python main.py
```

程序启动后，会自动在项目根目录创建 `detection_system.db` 数据库文件，并填充一些示例数据。

## 5. 项目结构

```
/
├── main.py                   # 程序主入口
├── main_window.py            # 主窗口UI定义
├── requirements.txt          # Python依赖包列表
├── detection_system.db       # SQLite数据库文件
├── modules/                  # 核心功能模块
│   ├── main_detection_view.py # 主检测视图UI
│   ├── realtime_chart.py     # 实时监控图表UI
│   ├── history_viewer.py     # 历史数据显示UI
│   ├── annotation_tool.py    # 缺陷标注工具UI
│   ├── models.py             # SQLAlchemy数据库模型
│   └── worker_thread.py      # 后台数据采集线程
├── hardware/                 # 硬件接口模块
│   └── CR1500_controller.py  # 模拟硬件控制器
└── docs/                     # 项目文档（非代码）
```
