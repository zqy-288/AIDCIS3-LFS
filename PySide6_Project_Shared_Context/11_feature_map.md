# 功能地图

本文件将“管孔检测系统”的核心功能映射到实现这些功能的相应源代码文件。

## 1. 主应用程序框架

- **功能**: 应用程序入口、初始化、主窗口管理。
- **文件**:
    - `main.py`: 应用程序的主入口点。处理依赖项检查、应用程序设置和主窗口的实例化。
    - `main_window.py`: 定义 `MainWindow` 类，这是应用程序的主 UI 框架。它包含选项卡控件，用于集成不同的功能模块。

## 2. 工件和孔的可视化

- **功能**: 显示工件上所有孔的布局图，并允许用户选择一个孔进行检测。
- **文件**:
    - `modules/main_detection_view.py`: 实现 `MainDetectionView` 类，该类使用 `QGraphicsView` 来绘制和管理孔的视觉表示。

## 3. 实时数据监控

- **功能**: 从传感器（或 CSV 文件）获取实时测量数据，并将其显示在动态图表上。
- **文件**:
    - `modules/realtime_chart.py`: 实现 `RealtimeChart` 类，该类使用 `pyqtgraph` 创建和管理实时数据图表。
    - `modules/worker_thread.py`: （当前用于模拟）定义 `WorkerThread` 类，用于在后台处理数据采集，以避免阻塞主 UI 线程。

## 4. 历史数据查看

- **功能**: 从数据库加载并显示历史测量数据，以供分析和审查。
- **文件**:
    - `modules/history_viewer.py`: 实现 `HistoryViewer` 类，提供用于选择和显示历史数据的 UI。

## 5. 缺陷标注

- **功能**: 提供一个工具，用于在内窥镜图像上加载、绘制和保存缺陷标注。
- **文件**:
    - `modules/annotation_tool.py`: 实现 `AnnotationTool` 类，包含图像显示和绘图功能。

## 6. 数据库和数据模型

- **功能**: 定义应用程序的数据结构，并处理与数据库的所有交互。
- **文件**:
    - `modules/models.py`: 使用 SQLAlchemy ORM 定义所有数据模型（`Workpiece`, `Hole`, `Measurement`, `Annotation` 等），并提供一个 `DatabaseManager` 来处理数据库操作。
    - `detection_system.db`: SQLite 数据库文件，是数据的最终存储位置。

## 7. 硬件接口

- **功能**: 与物理硬件（如传感器控制器）进行通信。
- **文件**:
    - `hardware/CR1500_controller.py`: （示例）与 CR1500 控制器通信的接口。
