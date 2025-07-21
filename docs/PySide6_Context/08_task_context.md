# 任务上下文

本文件概述了“管孔检测系统”应用程序执行的主要任务。这些任务共同构成了系统的核心功能。

## 1. 工件和孔管理

- **任务描述**: 系统能够管理工件及其上的孔。这包括创建、读取、更新和删除（CRUD）工件和孔的数据。
- **实现**: 
    - `modules/models.py`: 定义了 `Workpiece` 和 `Hole` 的 SQLAlchemy 模型。
    - `modules/main_detection_view.py`: 提供了一个可视化界面，用于显示工件上的孔布局。
    - `detection_system.db`: SQLite 数据库，用于存储工件和孔的数据。

## 2. 实时数据采集与监控

- **任务描述**: 从传感器（或通过 CSV 导入的模拟数据）实时采集孔的深度和直径数据，并在图表上进行可视化显示。
- **实现**:
    - `modules/realtime_chart.py`: 实现了用于显示实时数据的图表组件。
    - `modules/worker_thread.py`: （在当前版本中用于模拟）处理后台数据采集的线程。
    - `main_window.py`: 将实时图表集成到主窗口的“实时监控”选项卡中。

## 3. 历史数据查看与分析

- **任务描述**: 用户可以查看和分析之前检测任务中保存的历史数据。这包括按孔 ID 检索测量数据，并将其可视化。
- **实现**:
    - `modules/history_viewer.py`: 提供了查看历史数据的界面。
    - `modules/models.py`: `Measurement` 模型用于存储历史测量数据。
    - `main_window.py`: 将历史查看器集成到“历史数据”选项卡中。

## 4. 缺陷标注

- **任务描述**: 在内窥镜图像上对检测到的缺陷（如裂纹、腐蚀）进行标注。这对于训练机器学习模型或进行质量复核至关重要。
- **实现**:
    - `modules/annotation_tool.py`: 提供了缺陷标注的用户界面。
    - `modules/models.py`: `EndoscopeImage` 和 `Annotation` 模型用于存储图像和标注数据。
    - `main_window.py`: 将标注工具集成到“缺陷标注”选项卡中。

## 5. 数据持久化

- **任务描述**: 将所有应用程序数据（包括工件信息、测量数据、标注等）持久化到数据库中。
- **实现**:
    - `modules/models.py`: 定义了整个应用程序的数据模型，并使用 SQLAlchemy ORM 与数据库进行交互。
    - `detection_system.db`: 作为本地数据存储的 SQLite 数据库。
