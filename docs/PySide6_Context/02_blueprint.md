# 软件架构蓝图 (Blueprint)

**最后更新时间: 2025-07-07**

## 1. 架构概述

本系统采用基于 **PySide6** 的模块化桌面应用程序架构。其核心设计思想是将用户界面（View）、业务逻辑（Logic）和数据模型（Model）进行分离，以提高代码的可维护性和可扩展性。整体架构可以分为以下几个层次：

*   **表现层 (Presentation Layer)**: 由 `main_window.py` 和 `modules/` 目录下的各个UI模块组成，负责用户界面的展示和交互。
*   **业务逻辑层 (Business Logic Layer)**: 主要由 `worker_thread.py` 和各个UI模块内部的事件处理逻辑构成，负责处理核心功能，如数据采集、计算和流程控制。
*   **数据访问层 (Data Access Layer)**: 由 `modules/models.py` 实现，通过 `SQLAlchemy` ORM 框架与底层的 SQLite 数据库进行交互。
*   **硬件抽象层 (Hardware Abstraction Layer)**: 由 `hardware/CR1500_controller.py` 提供，用于封装与物理硬件的通信细节，并提供一个模拟接口。

## 2. 组件关系图

```mermaid
graph TD
    subgraph 用户界面 (UI Layer)
        A[main.py] --> B[MainWindow];
        B --> C{QTabWidget};
        C --> D[主检测视图 MainDetectionView];
        C --> E[实时监控 RealtimeChart];
        C --> F[历史数据 HistoryViewer];
        C --> G[缺陷标注 AnnotationTool];
    end

    subgraph 业务逻辑 (Business Logic)
        E -- 控制 --> H[后台线程 WorkerThread];
        E -- 导入数据 --> I[CSV文件];
        H -- 更新数据 --> E;
        D -- 导航 --> E;
        D -- 导航 --> F;
    end

    subgraph 数据与硬件 (Data & Hardware)
        J[数据库模块 models.py] <--> K[(detection_system.db)];
        H -- 模拟数据 --> L[硬件控制器 CR1500_controller];
        F -- 查询 --> J;
        G -- 加载/保存 --> M[图像文件];
    end

    F --> J;
    H --> L;
```

## 3. 核心组件说明

*   **`main.py`**: **程序入口**。负责初始化应用环境，检查依赖，创建数据库连接，并启动主窗口。

*   **`MainWindow`**: **主窗口容器**。作为应用程序的主框架，它不包含具体的业务逻辑，而是通过一个 `QTabWidget` 来容纳和管理不同的功能视图（`MainDetectionView`, `RealtimeChart` 等）。

*   **`MainDetectionView`**: **主检测视图/导航页**。这是应用的起始页面，提供了工件的整体视图，并作为导航入口，引导用户进入“实时监控”或“历史数据”页面。

*   **`RealtimeChart`**: **实时监控模块**。这是系统的核心功能之一。它负责：
    *   通过 `pyqtgraph` 创建和更新实时图表。
    *   管理 `WorkerThread` 的生命周期（启动/停止）。
    *   处理从CSV文件导入数据的逻辑。

*   **`HistoryViewer`**: **历史数据模块**。负责从数据库中查询和展示历史检测数据。它直接与 `models.py` 交互以获取数据。

*   **`AnnotationTool`**: **缺陷标注模块**。一个独立的工具，使用 `matplotlib` 作为画布，让用户可以在图像上进行绘制和标注。

*   **`WorkerThread`**: **后台工作线程**。通过 `QThread` 实现，用于处理耗时的数据采集任务，防止UI线程阻塞。它会调用硬件控制器来获取数据，并通过信号（`data_updated`）将数据发送给 `RealtimeChart` 进行更新。

*   **`models.py`**: **数据模型和管理器**。使用 `SQLAlchemy` 定义了所有数据库表的结构（如 `Workpiece`, `Hole`, `Measurement`），并提供 `DBManager` 类来封装所有数据库的CRUD（增删改查）操作。

*   **`CR1500_controller.py`**: **模拟硬件控制器**。它模拟了一个真实的硬件设备，能够生成符合预设格式的随机数据。这使得在没有物理硬件的情况下也能进行完整的软件功能测试。

## 4. 数据流

1.  **实时检测流程**: `RealtimeChart` 启动 `WorkerThread` -> `WorkerThread` 调用 `CR1500_controller` 生成数据 -> `WorkerThread` 发出 `data_updated` 信号 -> `RealtimeChart` 的槽函数接收信号并更新图表。
2.  **CSV导入流程**: 用户在 `RealtimeChart` 界面点击导入按钮 -> `RealtimeChart` 弹出文件对话框选择CSV文件 -> `RealtimeChart` 解析文件内容并更新图表。
3.  **历史数据查看流程**: 用户在 `HistoryViewer` 界面执行查询 -> `HistoryViewer` 调用 `DBManager` 的方法 -> `DBManager` 执行SQL查询并返回结果 -> `HistoryViewer` 将结果展示在UI上。
