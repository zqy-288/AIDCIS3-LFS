# 文件地图 (File Map)

**最后更新时间: 2025-07-07**

## 1. 项目根目录

```
/
├── main.py
├── main_window.py
├── requirements.txt
├── detection_system.db
├── modules/
├── hardware/
├── docs/
└── PySide6_Project_Shared_Context/
```

*   **`main.py`**: **程序主入口**。负责应用的初始化、依赖检查和启动主窗口。
*   **`main_window.py`**: **主窗口定义**。包含 `MainWindow` 类，是应用程序UI的顶层容器，通过 `QTabWidget` 管理各个功能页面。
*   **`requirements.txt`**: **Python依赖列表**。定义了项目运行所需的所有第三方库及其版本。
*   **`detection_system.db`**: **SQLite数据库文件**。在程序首次运行时自动创建，用于存储所有检测数据。

## 2. `modules/` - 核心功能模块

此目录包含了应用程序的所有核心业务逻辑和UI组件。

```
modules/
├── __init__.py
├── main_detection_view.py
├── realtime_chart.py
├── history_viewer.py
├── annotation_tool.py
├── models.py
├── worker_thread.py
├── workpiece_diagram.py
├── endoscope_view.py
└── matplotlib_chart.py
```

*   **`main_detection_view.py`**: 实现 `MainDetectionView` 类，作为应用程序的**主检测视图**和导航中心。
*   **`realtime_chart.py`**: 实现 `RealtimeChart` 类，负责**实时数据显示**。包含 `pyqtgraph` 图表和数据导入逻辑。
*   **`history_viewer.py`**: 实现 `HistoryViewer` 类，用于**历史数据的查询和展示**。
*   **`annotation_tool.py`**: 实现 `AnnotationTool` 类，一个基于Matplotlib的**缺陷标注工具**。
*   **`models.py`**: **数据库模型定义**。使用 SQLAlchemy ORM 定义了所有数据表（如工件、孔、测量等）的结构，并提供了 `DBManager` 进行数据库操作。
*   **`worker_thread.py`**: 定义 `WorkerThread` 类，用于在**后台执行数据采集**等耗时任务，避免UI阻塞。
*   **`workpiece_diagram.py`**: 一个可重用的UI组件，用于显示**工件的示意图**。
*   **`endoscope_view.py`**: 一个可重用的UI组件，可能用于显示**内窥镜图像**。
*   **`matplotlib_chart.py`**: 一个通用的 Matplotlib 图表封装组件，被 `AnnotationTool` 等模块使用。

## 3. `hardware/` - 硬件抽象层

此目录用于封装与具体硬件交互的逻辑。

```
hardware/
├── __init__.py
└── CR1500_controller.py
```

*   **`CR1500_controller.py`**: **模拟硬件控制器**。它提供了一个 `CR1500Controller` 类，该类模拟了真实硬件的行为，能够生成随机的测量数据。这使得软件可以在没有物理硬件连接的情况下进行开发和测试。

## 4. `docs/` 和 `PySide6_Project_Shared_Context/`

*   **`docs/`**: 包含项目相关的非代码文档，如用户手册、开发日志等。
*   **`PySide6_Project_Shared_Context/`**: 包含由AI工具维护的、与代码库同步的项目上下文和分析文档（例如本文档）。
